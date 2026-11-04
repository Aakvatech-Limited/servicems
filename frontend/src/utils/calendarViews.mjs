// Pure, timezone-stable calendar date and grouping helpers.
export function parseDay(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) throw new Error('Invalid date')
  const day = new Date(value + 'T00:00:00Z')
  if (Number.isNaN(day.getTime()) || day.toISOString().slice(0, 10) !== value)
    throw new Error('Invalid date')
  return day
}
export function addDays(value, amount) {
  const day = parseDay(value)
  day.setUTCDate(day.getUTCDate() + amount)
  return day.toISOString().slice(0, 10)
}
export function monday(value) {
  const day = parseDay(value)
  return addDays(value, -((day.getUTCDay() + 6) % 7))
}
export function monthStart(value) {
  parseDay(value)
  return value.slice(0, 7) + '-01'
}
export function formatDay(value, opts = {}) {
  return new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC', ...opts })
    .format(parseDay(value))
}
export function viewRange(date, view) {
  parseDay(date)
  if (view === 'day') return { from: date, to: date }
  if (view === 'week') {
    const from = monday(date)
    return { from, to: addDays(from, 6) }
  }
  if (view === 'month') {
    const from = monthStart(date)
    const next = new Date(Date.UTC(Number(from.slice(0, 4)), Number(from.slice(5, 7)), 1))
    return { from, to: addDays(next.toISOString().slice(0, 10), -1) }
  }
  throw new Error('Unsupported view')
}
export function shiftDate(date, view, direction) {
  if (view === 'day') return addDays(date, direction)
  if (view === 'week') return addDays(date, direction * 7)
  if (view === 'month') {
    const d = parseDay(date)
    const target = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + direction, 1))
    const last = new Date(Date.UTC(target.getUTCFullYear(), target.getUTCMonth() + 1, 0)).getUTCDate()
    target.setUTCDate(Math.min(d.getUTCDate(), last))
    return target.toISOString().slice(0, 10)
  }
  throw new Error('Unsupported view')
}
export function daysBetween(from, to) {
  const out = []
  for (let value = from; value <= to && out.length < 370; value = addDays(value, 1))
    out.push(value)
  return out
}
export function timeLabel(value) {
  const match = /^(\d{1,2}):(\d{2})(?::\d{2})?$/.exec(value || '')
  return match ? match[1].padStart(2, '0') + ':' + match[2] : 'Time not set'
}
export function rowGroups(bookings, baysEnabled, bays, workshop) {
  if (!baysEnabled)
    return [{ key: 'all', label: workshop || 'All bookings', entries: bookings }]
  const selected = (bays || []).map((bay) => ({
    key: 'bay:' + bay.name,
    label: bay.name,
    workshop: bay.service_workshop,
    entries: bookings.filter((row) => row.bay === bay.name),
  }))
  const known = new Set((bays || []).map((bay) => bay.name))
  const other = bookings.filter((row) => row.bay && !known.has(row.bay))
  if (other.length) selected.push({key: 'other', label: 'Other allocated Bays', entries: other})
  const unassigned = bookings.filter((row) => !row.bay)
  if (unassigned.length || !selected.length)
    selected.push({ key: 'unassigned', label: 'No Bay', entries: unassigned })
  return selected
}

export function siteToday(timeZone, now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-GB', {timeZone, year: 'numeric', month: '2-digit', day: '2-digit'}).formatToParts(now)
  const value = (type) => parts.find((part) => part.type === type).value
  return `${value('year')}-${value('month')}-${value('day')}`
}

export function rescheduleTimeValue(input, previous) {
  // A date-only edit must retain seconds that the minute-only control does not show.
  if (previous && input === timeLabel(previous))
    return input + ':' + (previous.split(':')[2] || '00')
  return input
}
