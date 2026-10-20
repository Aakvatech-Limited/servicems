import assert from 'node:assert/strict'
import { test } from 'node:test'
import { calendarDays, dateRange } from '../src/utils/bookingCalendar.mjs'

test('includes both endpoints and empty days across month boundaries', () => {
  const days = calendarDays(dateRange('2026-01-01', '2026-02-01'))
  assert.equal(days.length, 32)
  assert.equal(days[0].date, '2026-01-01')
  assert.equal(days.at(-1).date, '2026-02-01')
  assert.deepEqual(days[0].bookings, [])
})
test('defaults to seven days when To Date is empty', () => {
  assert.equal(dateRange('2026-12-29', '').to, '2027-01-04')
})
test('keeps multiple bookings on the same date without duplicating them on other dates', () => {
  const records = [
    { name: 'one', booking_date: '2026-01-01' },
    { name: 'two', booking_date: '2026-01-01' },
    { name: 'outside', booking_date: '2026-02-01' },
  ]
  const days = calendarDays(dateRange('2026-01-01', '2026-01-02'), records)
  assert.deepEqual(
    days[0].bookings.map((b) => b.name),
    ['one', 'two'],
  )
  assert.deepEqual(days[1].bookings, [])
  assert.equal(records.length, 3)
})
test('handles leap day and a one-day range', () => {
  assert.equal(calendarDays(dateRange('2028-02-28', '2028-03-01')).length, 3)
  assert.equal(calendarDays(dateRange('2026-01-01', '2026-01-01')).length, 1)
})
test('rejects invalid and reversed dates', () => {
  for (const dates of [
    ['not-a-date', ''],
    ['2026-02-30', ''],
    ['2026-02-01', '2026-01-01'],
  ]) {
    assert.ok(dateRange(...dates).error)
  }
})
test('bounds the date range without truncating valid ranges', () => {
  assert.equal(dateRange('2026-01-01', '2027-01-01').error, '')
  assert.ok(dateRange('2026-01-01', '2027-01-02').error)
})
test('keeps dates stable across daylight-saving changes', () => {
  const days = calendarDays(dateRange('2026-03-07', '2026-03-10'))
  assert.deepEqual(
    days.map((d) => d.date),
    ['2026-03-07', '2026-03-08', '2026-03-09', '2026-03-10'],
  )
})
