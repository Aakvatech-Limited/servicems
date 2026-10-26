import {
  addDays,
  differenceInCalendarDays,
  eachDayOfInterval,
  format,
  isValid,
  parseISO,
} from 'date-fns'

export function dateRange(from, to) {
  const start = parseISO(from)
  const end = to ? parseISO(to) : addDays(start, 6)
  if (!isValid(start) || !isValid(end))
    return { error: 'Select valid booking dates.' }
  const span = differenceInCalendarDays(end, start)
  if (span < 0) return { error: 'To Date must be on or after From Date.' }
  if (span > 365) return { error: 'Select a date range of at most 366 days.' }
  return {
    from: format(start, 'yyyy-MM-dd'),
    to: format(end, 'yyyy-MM-dd'),
    error: '',
  }
}

export function calendarDays(range, records = []) {
  const grouped = new Map()
  for (const booking of records) {
    const bookings = grouped.get(booking.booking_date) || []
    bookings.push(booking)
    grouped.set(booking.booking_date, bookings)
  }
  return eachDayOfInterval({
    start: parseISO(range.from),
    end: parseISO(range.to),
  }).map((day) => {
    const date = format(day, 'yyyy-MM-dd')
    return {
      date,
      label: format(day, 'EEE, d MMM'),
      bookings: grouped.get(date) || [],
    }
  })
}
