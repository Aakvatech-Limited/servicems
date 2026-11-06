export async function calendarWorkshops(request) {
  const names = []
  let page
  do {
    page = await request({
      url: 'servicems.api.calendar.get_calendar_workshops',
      method: 'GET',
      params: { start: names.length },
    })
    names.push(...page.map((row) => row.name))
  } while (page.length === 500)
  return names
}
