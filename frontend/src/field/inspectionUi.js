export const inspectionSteps = [
  { title: 'Vehicle', icon: 'truck' },
  { title: 'Checklist', icon: 'check-square' },
  { title: 'Photos', icon: 'camera' },
  { title: 'Findings', icon: 'map-pin' },
  { title: 'Review', icon: 'clipboard' },
]

export function formatCaptureTime(value) {
  if (!value) return '—'
  const match = String(value).match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/)
  if (!match) return String(value)
  const day = new Intl.DateTimeFormat('en', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(match[1] + 'T00:00:00Z'))
  return `${day} · ${match[2]}${
    String(value).endsWith('Z') ? ' UTC' : ' (site time)'
  }`
}

export function answerChoices(row) {
  return row.option
    ?.split(/\r?\n/)
    .map((value) => value.trim())
    .filter(Boolean).length
    ? row.option
        .split(/\r?\n/)
        .map((value) => value.trim())
        .filter(Boolean)
    : ['Yes', 'No', 'N/A']
}

export function inspectionIssues(inspection, checklist, values, photos) {
  const issues = []
  for (const row of checklist) {
    if (row.is_required && !String(row.answer || '').trim())
      issues.push({ step: 1, label: `Answer: ${row.inspection_item}` })
    if (row.require_photo && !row.photograph)
      issues.push({ step: 2, label: `Photo: ${row.inspection_item}` })
  }
  if (
    inspection.require_photographs_snapshot &&
    !photos.length &&
    !values.image_upload
  )
    issues.push({ step: 2, label: 'Add a stage photograph' })
  if (
    inspection.require_gps_snapshot &&
    (!values.gps_captured_at ||
      values.gps_latitude == null ||
      values.gps_longitude == null ||
      values.gps_accuracy == null)
  )
    issues.push({
      step: 3,
      label: 'Capture location with accuracy and timestamp',
    })
  return issues
}

export function stageRecord(records, stage) {
  const matches = records.filter((record) => record.inspection_stage === stage)
  return (
    matches.find((record) => record.inspection_status === 'Draft') ||
    matches[0] ||
    null
  )
}

export async function loadJobHistories(jobs, load, concurrency = 4) {
  const records = {},
    errors = []
  let next = 0
  await Promise.all(
    Array.from({ length: Math.min(concurrency, jobs.length) }, async () => {
      while (next < jobs.length) {
        const job = jobs[next++]
        try {
          records[job.name] = await load(job.name)
        } catch {
          errors.push(job.name)
        }
      }
    })
  )
  return { records, errors }
}
