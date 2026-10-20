import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'

const source = readFileSync(
  new URL(
    '../../servicems/service_management/doctype/service_booking/service_booking.js',
    import.meta.url,
  ),
  'utf8',
)

function loadHandlers(newDoc = () => {}) {
  let handlers
  vm.runInNewContext(source, {
    frappe: {
      ui: {
        form: {
          on: (_, events) => {
            handlers = events
          },
        },
      },
      new_doc: newDoc,
    },
    __: (value) => value,
  })
  return handlers
}

test('Close Booking marks the status dirty and returns the save promise', async () => {
  let close
  const calls = []
  const saved = Promise.resolve()
  const frm = {
    doc: { status: 'Pending' },
    is_new: () => false,
    add_custom_button: (_, callback) => {
      close = callback
    },
    refresh_field: (field) => calls.push(['refresh', field]),
    dirty: () => calls.push(['dirty']),
    save: () => {
      calls.push(['save'])
      return saved
    },
  }
  loadHandlers().close_booking(frm)
  assert.equal(close(), saved)
  assert.equal(frm.doc.status, 'Closed')
  assert.deepEqual(calls, [['refresh', 'status'], ['dirty'], ['save']])
  await saved
})

test('Close Booking is hidden for unsaved, closed and completed bookings', () => {
  for (const [isNew, status] of [
    [true, 'Pending'],
    [false, 'Closed'],
    [false, 'Completed'],
  ]) {
    loadHandlers().close_booking({
      doc: { status },
      is_new: () => isNew,
      add_custom_button: () => assert.fail('Unexpected Close Booking button'),
    })
  }
})

test('Create Job Card copies the booking references without requiring a bay', () => {
  let target, values
  const handlers = loadHandlers((doctype, defaults) => {
    target = doctype
    values = JSON.parse(JSON.stringify(defaults))
  })
  handlers.create_service_job_card_record({
    doc: {
      name: 'BOOKING',
      workshop: 'Garage',
      service_vehicle: 'VEHICLE',
      customer: 'Customer',
      phone_no: '123',
    },
  })
  assert.equal(target, 'Service Job Card')
  assert.deepEqual(values, {
    workshop: 'Garage',
    service_item_name: 'VEHICLE',
    customer: 'Customer',
    mobile_no: '123',
    service_booking: 'BOOKING',
  })
})

test('Job Card refresh completes and installs the parts query', async () => {
  let handlers,
    queryInstalled = false
  const frm = {
    doc: { docstatus: 0, parts: [] },
    fields_dict: {},
    is_dirty: () => false,
    add_custom_button: () => {},
    set_query: (field, table) => {
      queryInstalled = field === 'item' && table === 'parts'
    },
  }
  const jobCardSource = readFileSync(
    new URL(
      '../../servicems/service_management/doctype/service_job_card/service_job_card.js',
      import.meta.url,
    ),
    'utf8',
  )
  vm.runInNewContext(jobCardSource, {
    frappe: {
      ui: {
        form: {
          on: (_, events) => {
            handlers = events
          },
        },
      },
      db: { exists: async () => false },
    },
    cur_frm: frm,
  })
  assert.doesNotThrow(() => handlers.refresh(frm))
  assert.equal(queryInstalled, true)
  await Promise.resolve()
})
