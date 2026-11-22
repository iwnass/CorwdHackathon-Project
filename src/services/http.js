import { config } from '../config'

// Tiny fetch wrapper. Every backend call goes through here,
// so auth headers, logging or retries only need to be added once.
export async function http(path, { method = 'GET', body, params, signal } = {}) {
  const query = params ? `?${new URLSearchParams(params)}` : ''
  const res = await fetch(`${config.apiBaseUrl}${path}${query}`, {
    method,
    signal,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    const err = new Error(`API ${method} ${path} failed (${res.status}): ${text}`)
    err.status = res.status
    throw err
  }
  return res.status === 204 ? null : res.json()
}
