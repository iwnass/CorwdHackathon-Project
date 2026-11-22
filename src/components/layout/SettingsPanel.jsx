import { useEffect } from 'react'
import { useTheme } from '../../context/ThemeContext'
import { useLang } from '../../i18n/LanguageContext'
import { THEME_COLORS } from '../../utils/themes'
import { CheckIcon, CloseIcon, ContrastIcon, GlobeIcon, PaletteIcon, SettingsIcon, SunIcon } from '../ui/Icons'
import { DonateButton, ReportButton } from './Sidebar'

/**
 * Settings: light/dark mode (with mini previews), accent colour (re-tints the
 * whole app) and language.
 * Phones: slides up from the bottom. Tablet/desktop: slides in from the side.
 */
export default function SettingsPanel() {
  const { settingsOpen, setSettingsOpen, isDark, setIsDark, color, setColor, palette, showHeatmap, setShowHeatmap } = useTheme()
  const { t, lang, setLang, languages } = useLang()
  const close = () => setSettingsOpen(false)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && setSettingsOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [setSettingsOpen])

  return (
    <>
      <div
        onClick={close}
        className={`fixed inset-0 z-50 bg-black/40 backdrop-blur-[2px] transition-opacity duration-300 ${
          settingsOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      />

      <section
        role="dialog"
        aria-modal="true"
        aria-label={t('settings.title')}
        inert={!settingsOpen}
        className={`fixed z-50 flex flex-col overflow-hidden bg-surface shadow-2xl ring-1 ring-line transition-transform duration-300 ease-out
          inset-x-0 bottom-0 max-h-[88dvh] rounded-t-3xl
          md:inset-x-auto md:inset-y-3 md:end-3 md:max-h-none md:w-[22rem] md:rounded-3xl
          ${settingsOpen ? 'translate-y-0 md:translate-x-0' : 'translate-y-full md:translate-y-0 md:translate-x-[110%] md:rtl:-translate-x-[110%]'}`}
      >
        {/* Header in the theme colour */}
        <header className="relative shrink-0 overflow-hidden bg-gradient-to-br from-primary to-primary-dark px-5 pb-5 pt-3 text-white md:pt-5">
          <div className="pointer-events-none absolute -end-8 -top-10 h-36 w-36 rounded-full bg-white/10" />
          <div className="pointer-events-none absolute -bottom-12 end-16 h-24 w-24 rounded-full bg-white/10" />
          <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-white/40 md:hidden" />
          <div className="relative flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/20 backdrop-blur">
              <SettingsIcon className="h-5 w-5" />
            </span>
            <h2 className="flex-1 text-lg font-bold">{t('settings.title')}</h2>
            <button onClick={close} className="rounded-full p-2 transition hover:bg-white/20" aria-label={t('settings.close')}>
              <CloseIcon className="h-5 w-5" />
            </button>
          </div>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
          {/* Mode */}
          <Section icon={ContrastIcon} title={t('settings.mode')}>
            <div className="grid grid-cols-2 gap-3">
              {[
                { dark: false, label: t('settings.light') },
                { dark: true, label: t('settings.dark') },
              ].map((m) => (
                <button
                  key={m.label}
                  onClick={() => setIsDark(m.dark)}
                  aria-pressed={isDark === m.dark}
                  className={`group relative rounded-2xl p-1.5 text-start transition ${
                    isDark === m.dark ? 'bg-primary/10 ring-2 ring-primary' : 'ring-1 ring-line hover:ring-primary/50'
                  }`}
                >
                  <ModePreview dark={m.dark} accent={palette.primary} />
                  <span className="mt-1.5 flex items-center justify-between px-1 text-sm font-medium text-ink">
                    {m.label}
                    {isDark === m.dark && (
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-white">
                        <CheckIcon className="h-3.5 w-3.5" />
                      </span>
                    )}
                  </span>
                </button>
              ))}
            </div>
          </Section>

          {/* Colours */}
          <Section icon={PaletteIcon} title={t('settings.colors')}>
            <div className="grid grid-cols-6 gap-2.5">
              {Object.entries(THEME_COLORS).map(([name, c]) => (
                <button
                  key={name}
                  onClick={() => setColor(name)}
                  title={name}
                  aria-label={`${name} theme`}
                  aria-pressed={color === name}
                  className={`relative flex aspect-square items-center justify-center rounded-xl text-white shadow-sm transition ${
                    color === name ? 'scale-105 ring-2 ring-ink/30 ring-offset-2 ring-offset-surface' : 'hover:scale-105'
                  }`}
                  style={{ background: `linear-gradient(135deg, ${c.light}, ${c.dark})` }}
                >
                  {color === name && <CheckIcon className="h-4 w-4 drop-shadow" />}
                </button>
              ))}
            </div>
          </Section>

          {/* Heatmap on the map */}
          <Section icon={SunIcon} title={t('settings.heatmap')}>
            <button
              onClick={() => setShowHeatmap(!showHeatmap)}
              role="switch"
              aria-checked={showHeatmap}
              aria-label={t('settings.heatmap')}
              className="relative h-6 w-12 shrink-0 rounded-full bg-primary-lighter transition dark:bg-primary-darker"
            >
              <span
                className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all dark:bg-primary ${
                  showHeatmap ? 'left-6.5' : 'left-0.5'
                }`}
              />
            </button>
          </Section>

          {/* Language */}
          <Section icon={GlobeIcon} title={t('settings.language')}>
            <div className="grid grid-cols-2 gap-2">
              {languages.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLang(l.code)}
                  aria-pressed={lang === l.code}
                  lang={l.html}
                  className={`flex items-center justify-between gap-2 rounded-xl px-3 py-2 text-sm transition ${
                    lang === l.code
                      ? 'bg-primary font-semibold text-white shadow-md shadow-primary/30'
                      : 'bg-bg text-ink ring-1 ring-line hover:ring-primary/50'
                  }`}
                >
                  <span className="truncate">{l.label}</span>
                  <span className={`text-[10px] font-bold uppercase ${lang === l.code ? 'text-white/80' : 'text-muted'}`}>{l.code}</span>
                </button>
              ))}
            </div>
          </Section>

          {/* phones have no sidebar, so the donate button lives here */}
          <div className="flex gap-2 md:hidden">
            <DonateButton />
            <ReportButton />
          </div>
        </div>
      </section>
    </>
  )
}

function Section({ icon: Icon, title, children }) {
  return (
    <section className="rounded-2xl bg-bg/60 p-3.5 ring-1 ring-line">
      <h3 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted">
        <Icon className="h-4 w-4 text-primary" />
        {title}
      </h3>
      {children}
    </section>
  )
}

// Tiny mock of the app in light or dark mode, using the current accent colour
function ModePreview({ dark, accent }) {
  const bg = dark ? '#0b0f19' : '#f8fafc'
  const card = dark ? '#1e293b' : '#ffffff'
  const line = dark ? '#334155' : '#e2e8f0'
  return (
    <div className="flex h-16 gap-1 overflow-hidden rounded-xl p-1.5" style={{ background: bg }} aria-hidden="true">
      <div className="w-1/4 space-y-1 rounded-md p-1" style={{ background: card }}>
        <div className="h-1.5 rounded-full" style={{ background: accent }} />
        <div className="h-1 rounded-full" style={{ background: line }} />
        <div className="h-1 rounded-full" style={{ background: line }} />
      </div>
      <div className="flex flex-1 flex-col gap-1">
        <div className="h-3 rounded-md" style={{ background: card }} />
        <div className="flex flex-1 gap-1">
          <div className="flex-1 rounded-md" style={{ background: card }}>
            <div className="m-1 h-3 w-2/3 rounded-sm" style={{ background: accent, opacity: 0.7 }} />
          </div>
          <div className="w-1/3 rounded-md" style={{ background: card }} />
        </div>
      </div>
    </div>
  )
}
