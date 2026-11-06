/* ServiceMS Field PWA service worker.
 * Only static resources qualify for caching. Private API responses, File
 * downloads, session HTML, photographs and drafts are never cached.
 */
const CACHE = 'servicems-field-shell-v1'
self.addEventListener('install', (event) => {
  self.skipWaiting()
})
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(async (keys) => {
      await Promise.all(keys.filter((key) => key.startsWith('servicems-field-') && key !== CACHE).map((key) => caches.delete(key)))
      await self.clients.claim()
    })
  )
})
self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  // Network-only for all HTML, Frappe APIs, uploads, private downloads,
  // dynamically returned record data, images and customer files.
  if (request.mode === 'navigate' || !url.pathname.startsWith('/assets/servicems/')) return
  if (!/\.(?:js|css|woff2?|svg)$/.test(url.pathname)) return
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const saved = await cache.match(request)
      if (saved) return saved
      const response = await fetch(request)
      if (response.ok && response.type === 'basic') await cache.put(request, response.clone())
      return response
    })
  )
})
