import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'

const source = readFileSync(new URL('../../servicems/service_management/page/service_booking_calendar/service_booking_calendar.js', import.meta.url), 'utf8')

test('embedded calendar inherits resolved Desk dark surfaces and resets on light', () => {
  let theme = 'dark'
  const values = new Map()
  const listeners = {}
  const tokens = {
    '--bg-color': '#141414',
    '--fg-color': '#141414',
    '--subtle-fg': '#1f1f1f',
    '--control-bg': '#292929',
    '--border-color': '#343434',
    '--text-color': '#f8f8f8',
    '--text-muted': '#999999',
  }
  const root = {
    getAttribute: (name) => name === 'data-theme' ? theme : null,
    classList: { contains: () => false },
  }
  const embeddedRoot = {
    dataset: {},
    classList: { toggle: () => {} },
    style: {
      setProperty: (key, value) => values.set(key, value),
      removeProperty: (key) => values.delete(key),
    },
  }
  const frame = {
    contentDocument: { documentElement: embeddedRoot },
    contentWindow: { dispatchEvent: () => {} },
    addEventListener: (name, listener) => { listeners[name] = listener },
    getBoundingClientRect: () => ({ top: 100 }),
    style: {},
  }
  const wrapper = {
    classList: { add: () => {} },
    appendChild: () => {},
    getClientRects: () => [1],
  }
  const frappe = {
    pages: { 'service-booking-calendar': {} },
    ui: { make_app_page: () => ({ main: { empty: () => ({ append: () => {} }) } }) },
  }
  runInNewContext(source, {
    frappe,
    __: (value) => value,
    $: () => ({ on: () => {} }),
    document: {
      documentElement: root,
      body: root,
      createElement: (tag) => tag === 'iframe' ? frame : {},
    },
    getComputedStyle: () => ({
      fontFamily: 'Inter',
      colorScheme: theme,
      getPropertyValue: (key) => tokens[key] || '',
    }),
    CSS: { supports: (_, value) => /^#[0-9a-f]{6}$/i.test(value) },
    window: { innerHeight: 900 },
    Event: class {},
  })
  frappe.pages['service-booking-calendar'].on_page_load(wrapper)
  listeners.load()
  assert.equal(embeddedRoot.dataset.theme, 'dark')
  assert.equal(values.get('--sm-bg'), tokens['--bg-color'])
  assert.equal(values.get('--sm-surface'), tokens['--fg-color'])
  assert.equal(values.get('--sm-control-bg'), tokens['--control-bg'])
  assert.equal(values.get('--sm-border'), tokens['--border-color'])
  assert.equal(values.get('--sm-foreground'), tokens['--text-color'])
  tokens['--bg-color'] = '#181818'
  listeners.load()
  assert.equal(values.get('--sm-bg'), '#181818')
  theme = 'light'
  listeners.load()
  assert.equal(embeddedRoot.dataset.theme, 'light')
  assert.equal(values.has('--sm-bg'), false)
  assert.equal(values.has('--sm-control-bg'), false)
})
