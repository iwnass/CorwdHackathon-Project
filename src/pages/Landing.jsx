import { Link } from 'react-router-dom'
import DepthText from '../components/landing/DepthText'
import GradientWaves from '../components/landing/GradientWaves'
import ParthenonBackdrop from '../components/landing/ParthenonBackdrop'
import StickerBomb from '../components/landing/StickerBomb'
import LanguageSwitch from '../components/layout/LanguageSwitch'
import { useNavItems } from '../components/layout/navItems'
import { useLang } from '../i18n/LanguageContext'

// First screen the user sees. The buttons open the app's sections.
export default function Landing() {
  const { t } = useLang()
  const items = useNavItems().filter((i) => i.to !== '/heat')

  return (
    <div className="relative h-full overflow-y-auto bg-[#120f17] font-landing text-[#f1ecfa]">
      <GradientWaves />
      <StickerBomb />

      <div className="fixed end-4 top-4 z-10">
        <LanguageSwitch variant="dark" />
      </div>

      <div className="relative z-[2] flex min-h-full flex-col">
        <main className="box-border flex flex-1 flex-col items-center justify-center gap-8 px-5 py-8 text-center">
          {/* title with the faint Parthenon behind it */}
          <div className="relative isolate w-fit">
            <ParthenonBackdrop />
            <DepthText text="Athens Pulse" faceColor="#2ac2cc" depthColor="#652ad0" />
          </div>
          <p className="m-0 max-w-[34ch] text-lg leading-normal text-[#d6cfe6]">{t('landing.tagline')}</p>

          <nav aria-label={t('landing.links')} className="flex flex-wrap justify-center gap-3">
            {items.map(({ to, key, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className="flex items-center gap-2 rounded-full border-[1.5px] border-[#54c7ce]/60 bg-[#120f17]/55 px-[1.4rem] py-[0.8rem] font-semibold text-[#f1ecfa] no-underline backdrop-blur-[6px] transition-colors duration-200 hover:border-[#54c7ce] hover:bg-[#652ad0]/55 focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-[#54c7ce]"
              >
                <Icon className="h-5 w-5 opacity-80" />
                {t(key)}
              </Link>
            ))}
          </nav>
        </main>

        {/* team footer */}
        <footer className="px-4 pb-4 pt-2 text-center">
          <span className="font-brand text-base tracking-wide text-[#f1ecfa] drop-shadow-[0_2px_6px_rgba(0,0,0,0.7)] sm:text-lg">
            404 Brain Not Found
          </span>
        </footer>
      </div>
    </div>
  )
}
