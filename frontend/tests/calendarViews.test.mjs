import assert from 'node:assert/strict'
import { test } from 'node:test'
import { addDays, daysBetween, monday, monthStart, rowGroups, shiftDate, timeLabel, viewRange } from '../src/utils/calendarViews.mjs'

test('week starts Monday and spans seven days', () => {
  assert.deepEqual(viewRange('2026-11-05', 'week'), {
    from: '2026-11-02', to: '2026-11-08',
  })
  assert.equal(monday('2026-11-08'), '2026-11-02')
  assert.equal(daysBetween('2026-11-02', '2026-11-08').length, 7)
})
test('day and month views preserve the date bounds', () => {
  assert.deepEqual(viewRange('2026-11-05', 'day'), {from: '2026-11-05', to: '2026-11-05'})
  assert.deepEqual(viewRange('2026-11-05', 'month'), {from: '2026-11-01', to: '2026-11-30'})
  assert.equal(monthStart('2026-11-05'), '2026-11-01')
})
test('month navigation clamps end-of-month dates', () => {
  assert.equal(shiftDate('2026-01-31', 'month', 1), '2026-02-28')
  assert.equal(shiftDate('2028-01-31', 'month', 1), '2028-02-29')
})
test('date stepping crosses year boundaries safely', () => {
  assert.equal(addDays('2026-12-31', 1), '2027-01-01')
  assert.equal(shiftDate('2026-12-31', 'week', 1), '2027-01-07')
})
test('optional Bay Management renders all bookings without a Bay', () => {
  const rows = [{name: 'one', bay: ''}, {name: 'two', bay: 'Bay-1'}]
  const groups = rowGroups(rows, false, [], 'Workshop A')
  assert.equal(groups.length, 1)
  assert.deepEqual(groups[0].entries, rows)
})
test('enabled Bay Management includes an unallocated row', () => {
  const rows = [{name: 'one', bay: ''}, {name: 'two', bay: 'Bay-1'}]
  const groups = rowGroups(rows, true, [{name: 'Bay-1', service_workshop: 'Workshop A'}], '')
  assert.equal(groups.length, 2)
  assert.equal(groups[0].entries[0].name, 'two')
  assert.equal(groups[1].entries[0].name, 'one')
})
test('booking time displays the stored start only', () => {
  assert.equal(timeLabel('09:30:00'), '09:30')
  assert.equal(timeLabel(''), 'Time not set')
})
test('invalid dates cannot silently roll over', () => {
  assert.throws(() => viewRange('2026-02-30', 'day'))
})
