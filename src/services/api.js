/**
 * THE ONLY FILE THE BACKEND TEAM NEEDS TO TOUCH.
 *
 * Every function returns a Promise with the data shape documented in
 * mockData.js. With VITE_USE_MOCKS=true the mocks are used; set it to false
 * and the same functions call the real endpoints below.
 *
 * `lang` is 'en' or 'el' and is sent as ?lang=… so the backend can return
 * place names / event titles / agent replies in the user's language.
 * If an endpoint path or response shape differs, adapt it here — the
 * components won't need to change.
 */
import { config } from '../config'
import { http } from './http'
import { mock } from './mockData'

const real = {
  getEvents: (lang) => http('/events', { params: { lang } }),
  getTransitLines: (lang) => http('/transit/lines', { params: { lang } }),
  getTransitStations: (lang) => http('/transit/stations', { params: { lang } }),
  getEvStations: (lang) => http('/ev/stations', { params: { lang } }),
  getEvUsage: (lang) => http('/ev/usage', { params: { lang } }),
  askAgent: (message, history = [], lang) =>
    http('/agent/chat', { method: 'POST', body: { message, history, lang } }),
}

export const api = config.useMocks ? mock : real
