// All supported languages. To add one: create locales/<code>.js with the same
// keys as locales/en.js, then add it to LANGUAGES below.
import ar from './locales/ar'
import de from './locales/de'
import el from './locales/el'
import en from './locales/en'
import es from './locales/es'
import fr from './locales/fr'
import it from './locales/it'
import ja from './locales/ja'
import ru from './locales/ru'
import zh from './locales/zh'

export const translations = { en, el, it, de, fr, es, ru, zh, ja, ar }

/**
 * code      – our id (sent to the backend as ?lang=)
 * label     – native name shown in the language picker
 * html      – <html lang> value
 * locale    – for dates / numbers / currency (Intl)
 * dir       – text direction (Arabic is right-to-left)
 * maps      – Google Maps `hl` parameter
 * font      – extra Google Font for scripts Noto Sans doesn't cover
 */
export const LANGUAGES = [
  { code: 'en', label: 'English',  html: 'en',      locale: 'en-GB',           dir: 'ltr', maps: 'en' },
  { code: 'el', label: 'Ελληνικά', html: 'el',      locale: 'el-GR',           dir: 'ltr', maps: 'el' },
  { code: 'it', label: 'Italiano', html: 'it',      locale: 'it-IT',           dir: 'ltr', maps: 'it' },
  { code: 'de', label: 'Deutsch',  html: 'de',      locale: 'de-DE',           dir: 'ltr', maps: 'de' },
  { code: 'fr', label: 'Français', html: 'fr',      locale: 'fr-FR',           dir: 'ltr', maps: 'fr' },
  { code: 'es', label: 'Español',  html: 'es',      locale: 'es-ES',           dir: 'ltr', maps: 'es' },
  { code: 'ru', label: 'Русский',  html: 'ru',      locale: 'ru-RU',           dir: 'ltr', maps: 'ru' },
  { code: 'zh', label: '繁體中文', html: 'zh-Hant', locale: 'zh-TW',           dir: 'ltr', maps: 'zh-TW', font: 'Noto+Sans+TC' },
  { code: 'ja', label: '日本語',   html: 'ja',      locale: 'ja-JP',           dir: 'ltr', maps: 'ja',    font: 'Noto+Sans+JP' },
  { code: 'ar', label: 'العربية',  html: 'ar',      locale: 'ar-EG-u-nu-latn', dir: 'rtl', maps: 'ar',    font: 'Noto+Sans+Arabic' },
]

export const LANG_BY_CODE = Object.fromEntries(LANGUAGES.map((l) => [l.code, l]))
