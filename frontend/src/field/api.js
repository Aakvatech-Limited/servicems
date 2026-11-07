// Frappe session cookies and CSRF token; no browser storage of private records.
export async function api(method, params = {}, post = false) {
  const url = '/api/method/' + method
  const options = {
    method: post ? 'POST' : 'GET',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: {},
  }
  if (post) {
    options.headers['Content-Type'] = 'application/json'
    options.headers['X-Frappe-CSRF-Token'] = window.csrf_token
    options.body = JSON.stringify(params)
  } else {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) query.set(key, value)
    })
    options.headers['Accept'] = 'application/json'
    options.cache = 'no-store'
    const response = await fetch(
      url + (query.toString() ? '?' + query : ''),
      options
    )
    return unwrap(response)
  }
  return unwrap(await fetch(url, options))
}

async function unwrap(response) {
  if (response.status === 401 || response.status === 403)
    throw new Error(
      'Access denied. Sign in with an authorized ServiceMS account.'
    )
  const data = await response.json().catch(() => ({}))
  if (!response.ok || data.exc) {
    const errors = data._server_messages
      ? JSON.parse(data._server_messages)
      : []
    const message = errors.length ? JSON.parse(errors[0]).message : data.message
    throw new Error(
      message || 'Request failed. Check your connection and retry.'
    )
  }
  return data.message
}

export function uploadPhoto(file, inspection, onProgress) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    form.append('file', file)
    form.append('name', inspection)
    const request = new XMLHttpRequest()
    request.open(
      'POST',
      '/api/method/servicems.field_api.upload_inspection_photo'
    )
    request.withCredentials = true
    request.setRequestHeader('X-Frappe-CSRF-Token', window.csrf_token)
    request.upload.onprogress = (event) => {
      if (event.lengthComputable)
        onProgress?.(Math.round((event.loaded / event.total) * 100))
    }
    request.onload = () => {
      try {
        const result = JSON.parse(request.responseText)
        if (
          request.status >= 200 &&
          request.status < 300 &&
          result.message?.is_private
        )
          resolve(result.message)
        else {
          const messages = result._server_messages
            ? JSON.parse(result._server_messages)
            : []
          const message = messages.length
            ? JSON.parse(messages[messages.length - 1]).message
            : null
          reject(
            new Error(
              message ||
                'Private photo upload failed. Reopen the inspection and retry.'
            )
          )
        }
      } catch (_) {
        reject(new Error('Photo upload did not return a valid response.'))
      }
    }
    request.onerror = () =>
      reject(new Error('Connection interrupted while uploading photograph.'))
    request.send(form)
  })
}
