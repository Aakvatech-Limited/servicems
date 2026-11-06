import assert from 'node:assert/strict'
import { test } from 'node:test'
import { calendarWorkshops } from '../src/utils/calendarWorkshops.mjs'

test('Workshop options reach records beyond the first 500', async () => {
  const rows = Array.from({ length: 1001 }, (_, index) => ({ name: `Workshop ${index}` }))
  const starts = []
  const result = await calendarWorkshops(async ({ params }) => {
    starts.push(params.start)
    return rows.slice(params.start, params.start + 500)
  })
  assert.deepEqual(starts, [0, 500, 1000])
  assert.deepEqual(result, rows.map((row) => row.name))
})

test('users without Workshop access receive no options and do not request extra pages', async () => {
  let calls = 0
  assert.deepEqual(await calendarWorkshops(async () => { calls++; return [] }), [])
  assert.equal(calls, 1)
})

test('an optional Workshop lookup failure can be isolated from calendar loading', async () => {
  const [bookings, workshops] = await Promise.all([
    Promise.resolve([{ name: 'Permitted Booking' }]),
    calendarWorkshops(async () => { throw new Error('Workshop permission revoked') }).catch(() => []),
  ])
  assert.equal(bookings[0].name, 'Permitted Booking')
  assert.deepEqual(workshops, [])
})
