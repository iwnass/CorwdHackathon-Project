import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'

// Pages are lazy-loaded; a skeleton is shown while each one loads.
const Landing = lazy(() => import('./pages/Landing'))
const Transit = lazy(() => import('./pages/Transit'))
const Events = lazy(() => import('./pages/Events'))
const EvCharging = lazy(() => import('./pages/EvCharging'))

export default function App() {
  return (
    <Routes>
      {/* Landing page: the first thing users see */}
      <Route
        index
        element={
          <Suspense fallback={<div className="h-full bg-[#120f17]" />}>
            <Landing />
          </Suspense>
        }
      />

      {/* The app (sidebar + header) */}
      <Route element={<Layout />}>
        <Route path="events" element={<Events />} />
        <Route path="transit" element={<Transit />} />
        <Route path="ev-charging" element={<EvCharging />} />
        {/* old links */}
        <Route path="traffic" element={<Navigate to="/ev-charging" replace />} />
        <Route path="air" element={<Navigate to="/transit" replace />} />
        <Route path="analytics" element={<Navigate to="/transit" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
