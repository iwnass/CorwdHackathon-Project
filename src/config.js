// All environment-driven settings in one place. See .env.example
export const config = {
  useMocks: import.meta.env.VITE_USE_MOCKS !== 'false',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  donateUrl: import.meta.env.VITE_DONATE_URL || 'https://www.buymeacoffee.com/',
  googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '',
  // MapTiler (maptiler.com) key for the map
  maptilerKey: import.meta.env.VITE_MAPTILER_KEY || '',
  // Center of the Municipality of Athens
  athensCenter: { lat: 37.9838, lng: 23.7275 },
}
