import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { AppLayout } from './layouts/AppLayout'
import { DashboardPage } from './pages/DashboardPage'
import { EndpointsPage } from './pages/EndpointsPage'
import { FindingDetailPage } from './pages/FindingDetailPage'
import { FindingsPage } from './pages/FindingsPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ScanDetailPage } from './pages/ScanDetailPage'
import { ScansPage } from './pages/ScansPage'
import { ComparePage } from './pages/ComparePage'
import { EndpointsHubPage } from './pages/EndpointsHubPage'
import { FindingsHubPage } from './pages/FindingsHubPage'
import { RegressionHubPage } from './pages/RegressionHubPage'
import { LoadingState } from './components/LoadingState'

function PublicOnly({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <LoadingState label="Loading…" />
      </div>
    )
  }
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicOnly>
                <LoginPage />
              </PublicOnly>
            }
          />
          <Route
            path="/register"
            element={
              <PublicOnly>
                <RegisterPage />
              </PublicOnly>
            }
          />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/scans" element={<ScansPage />} />
              <Route path="/endpoints" element={<EndpointsHubPage />} />
              <Route path="/findings" element={<FindingsHubPage />} />
              <Route path="/regression" element={<RegressionHubPage />} />
              <Route path="/scans/:scanId" element={<ScanDetailPage />} />
              <Route path="/scans/:scanId/compare" element={<ComparePage />} />
              <Route path="/scans/:scanId/compare/:baselineScanId" element={<ComparePage />} />
              <Route path="/scans/:scanId/endpoints" element={<EndpointsPage />} />
              <Route path="/scans/:scanId/findings" element={<FindingsPage />} />
              <Route path="/scans/:scanId/findings/:findingId" element={<FindingDetailPage />} />
            </Route>
          </Route>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  )
}
