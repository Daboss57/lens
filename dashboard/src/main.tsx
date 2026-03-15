import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import './index.css'
import { AppShell } from './ui/app-shell'

const LiveFeedPage = lazy(() => import('./views/live-feed-page').then((module) => ({ default: module.LiveFeedPage })))
const CostTrackerPage = lazy(() => import('./views/cost-tracker-page').then((module) => ({ default: module.CostTrackerPage })))
const FailuresPage = lazy(() => import('./views/failures-page').then((module) => ({ default: module.FailuresPage })))
const SessionsPage = lazy(() => import('./views/sessions-page').then((module) => ({ default: module.SessionsPage })))
const DemoFlowPage = lazy(() => import('./views/demo-flow-page').then((module) => ({ default: module.DemoFlowPage })))

function RouteFallback() {
  return (
    <div className="panel-card p-6 text-sm text-muted">
      Loading workspace...
    </div>
  )
}

function withSuspense(element: React.ReactNode) {
  return <Suspense fallback={<RouteFallback />}>{element}</Suspense>
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: withSuspense(<LiveFeedPage />) },
      { path: 'costs', element: withSuspense(<CostTrackerPage />) },
      { path: 'failures', element: withSuspense(<FailuresPage />) },
      { path: 'sessions', element: withSuspense(<SessionsPage />) },
      { path: 'demo', element: withSuspense(<DemoFlowPage />) },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
