const tones = {
  neutral: 'bg-gray-100 text-gray-600 dark:bg-white/10 dark:text-gray-300',
  primary: 'bg-primary-100 text-primary-700 dark:bg-primary-500/15 dark:text-primary-300',
  success: 'bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-400',
  warning: 'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400',
  danger: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400',
}

// Pass `tone` for a preset, or `className` for a custom colour (e.g. AQI categories)
export function Badge({ tone = 'neutral', className = '', children }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${className || tones[tone]}`}>
      {children}
    </span>
  )
}
