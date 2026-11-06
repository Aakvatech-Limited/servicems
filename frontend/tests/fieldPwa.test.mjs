import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import { api, uploadPhoto } from '../src/field/api.js'

test('Field reads are same-origin and never stored by fetch', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(options.cache, 'no-store')
    assert.equal(options.credentials, 'same-origin')
    assert(url.includes('job_card=SJC+1'))
    return Response.json({ message: { name: 'SJC 1' } })
  })
  assert.equal((await api('servicems.field_api.get_field_job', { job_card: 'SJC 1' })).name, 'SJC 1')
})

test('Field draft writes carry CSRF and the concurrency token', async (t) => {
  globalThis.window = { csrf_token: 'test-token' }
  t.after(() => { delete globalThis.window })
  t.mock.method(globalThis, 'fetch', async (_, options) => {
    assert.equal(options.method, 'POST')
    assert.equal(options.headers['X-Frappe-CSRF-Token'], 'test-token')
    assert.equal(JSON.parse(options.body).expected_modified, 'previous-modified')
    return Response.json({ message: { name: 'SVI1' } })
  })
  await api('servicems.field_api.save_field_draft', { name: 'SVI1', expected_modified: 'previous-modified' }, true)
})

test('permission failures never masquerade as a successful save', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({}, { status: 403 }))
  await assert.rejects(api('servicems.field_api.get_field_job'), /Access denied/)
})

test('photo uploader binds the inspection using the guarded endpoint and reports progress', async (t) => {
  globalThis.window = { csrf_token: 'test-token' }
  globalThis.XMLHttpRequest = class {
    upload = {}
    open(method, url) { assert.equal(method, 'POST'); assert.equal(url, '/api/method/servicems.field_api.upload_inspection_photo') }
    setRequestHeader(name, value) { assert.equal(name, 'X-Frappe-CSRF-Token'); assert.equal(value, 'test-token') }
    send(form) {
      assert.equal(form.get('name'), 'SVI1')
      assert.equal(form.get('attached_to_name'), null)
      this.upload.onprogress({ lengthComputable: true, loaded: 5, total: 10 })
      this.status = 200
      this.responseText = JSON.stringify({ message: { is_private: 1, file_url: '/private/files/test.png' } })
      this.onload()
    }
  }
  t.after(() => { delete globalThis.window; delete globalThis.XMLHttpRequest })
  const progress = []
  await uploadPhoto(new File(['image'], 'test.png', { type: 'image/png' }), 'SVI1', (value) => progress.push(value))
  assert.deepEqual(progress, [50])
})

test('service worker ignores private routes, session HTML, photos, POST and query credentials', async () => {
  const listeners = {}
  let handled = 0
  runInNewContext(readFileSync(new URL('../../servicems/www/field-sw.js', import.meta.url), 'utf8'), {
    self: { location: { origin: 'https://test.invalid' }, addEventListener: (name, listener) => { listeners[name] = listener } }, URL,
  })
  for (const [path, method, mode] of [
    ['/field', 'GET', 'navigate'], ['/api/method/servicems.field_api.get_field_jobs', 'GET', 'cors'],
    ['/private/files/photo.png', 'GET', 'cors'], ['/files/photo.jpg', 'GET', 'cors'],
    ['/login', 'GET', 'navigate'], ['/assets/servicems/frontend/a.js?sid=secret', 'GET', 'cors'],
    ['/api/method/upload_file', 'POST', 'cors'],
  ]) {
    listeners.fetch({ request: { url: 'https://test.invalid' + path, method, mode }, respondWith: () => { handled++ } })
  }
  assert.equal(handled, 0)
})
