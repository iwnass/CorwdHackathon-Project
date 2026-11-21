import { useLang } from '../../i18n/LanguageContext'
import { MapPinIcon } from './Icons'

// Round "location point" button used on every event / EV station
export default function LocateButton({ onClick, active = false, className = '' }) {
  const { t } = useLang()
  return (
    <button
      onClick={onClick}
      aria-label={t('map.locate')}
      title={t('map.locate')}
      aria-pressed={active}
      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition ${
        active
          ? 'bg-primary text-white shadow-md shadow-primary/30'
          : 'bg-primary/15 text-primary-dark hover:bg-primary hover:text-white dark:text-primary-light'
      } ${className}`}
    >
      <MapPinIcon className="h-5 w-5" />
    </button>
  )
}
