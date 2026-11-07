import assert from 'node:assert/strict'
import { test } from 'node:test'
import { answerChoices, formatCaptureTime, inspectionIssues, loadJobHistories, stageRecord, inspectionSteps } from '../src/field/inspectionUi.js'

test('capture labels preserve UTC and naive site times without guessing a browser offset', () => {
  assert.equal(formatCaptureTime('2026-11-07T13:24:05.270Z'), 'Nov 7, 2026 · 13:24 UTC')
  assert.equal(formatCaptureTime('2026-11-07 16:24:05.270471'), 'Nov 7, 2026 · 16:24 (site time)')
})

test('guided steps retain the five required inspection sections', () => {
  assert.deepEqual(inspectionSteps.map(step => step.title), ['Vehicle', 'Checklist', 'Photos', 'Findings', 'Review'])
})

test('configured checklist choices retain exact backend values', () => {
  assert.deepEqual(answerChoices({ option: 'Pass\r\nFail\r\nN/A' }), ['Pass', 'Fail', 'N/A'])
  assert.deepEqual(answerChoices({ option: '  \n' }), ['Yes', 'No', 'N/A'])
})

test('optional photographs and GPS never block review completion', () => {
  assert.deepEqual(inspectionIssues({}, [{ inspection_item: 'Lights', is_required: 1, answer: 'N/A' }], {}, []), [])
})

test('review finds frozen item, stage photograph and GPS requirements', () => {
  const inspection = { require_photographs_snapshot: 1, require_gps_snapshot: 1 }
  const rows = [{ inspection_item: 'Tyres', is_required: 1, require_photo: 1 }]
  assert.deepEqual(inspectionIssues(inspection, rows, {}, []).map(issue => issue.step), [1, 2, 2, 3])
  const values = { gps_latitude: 0, gps_longitude: 0, gps_accuracy: 0, gps_captured_at: '2026-11-07' }
  assert.deepEqual(inspectionIssues(inspection, [{ ...rows[0], answer: 'Pass', photograph: '/private/files/tyres.png' }], values, [{ file_url: '/private/files/tyres.png' }]), [])
})

test('draft resume takes precedence over a completed stage without inventing statuses', () => {
  const records = [{ name: 'completed', inspection_stage: 'Pre-Service', inspection_status: 'Completed' }, { name: 'draft', inspection_stage: 'Pre-Service', inspection_status: 'Draft' }]
  assert.equal(stageRecord(records, 'Pre-Service').name, 'draft')
  assert.equal(stageRecord(records, 'Post-Service'), null)
})

test('dashboard loads only supplied permitted Job Cards with bounded concurrency and visible failures', async () => {
  let active = 0, maximum = 0
  const jobs = Array.from({ length: 12 }, (_, i) => ({ name: 'assigned-' + i }))
  const result = await loadJobHistories(jobs, async name => {
    assert(jobs.some(job => job.name === name))
    active++; maximum = Math.max(maximum, active)
    await new Promise(resolve => setTimeout(resolve, 5)); active--
    if (name === 'assigned-5') throw Error('Denied')
    return [{ name: 'inspection-' + name }]
  })
  assert(maximum <= 4)
  assert.equal(Object.keys(result.records).length, 11)
  assert.deepEqual(result.errors, ['assigned-5'])
})
