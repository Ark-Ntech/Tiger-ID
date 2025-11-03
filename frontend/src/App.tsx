import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/auth/ProtectedRoute'
import ErrorBoundary from './components/common/ErrorBoundary'

// Pages (will be created)
import Login from './pages/Login'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Investigations from './pages/Investigations'
import InvestigationWorkspace from './pages/InvestigationWorkspace'
import LaunchInvestigation from './pages/LaunchInvestigation'
import Tigers from './pages/Tigers'
import Facilities from './pages/Facilities'
import Verification from './pages/Verification'
import InvestigationTools from './pages/InvestigationTools'
import Templates from './pages/Templates'
import SavedSearches from './pages/SavedSearches'
import PasswordReset from './pages/PasswordReset'

function App() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/password-reset" element={<PasswordReset />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="investigations" element={<Investigations />} />
          <Route path="investigations/:id" element={<InvestigationWorkspace />} />
          <Route path="investigations/launch" element={<LaunchInvestigation />} />
          <Route path="tigers" element={<Tigers />} />
          <Route path="facilities" element={<Facilities />} />
          <Route path="verification" element={<Verification />} />
          <Route path="tools" element={<InvestigationTools />} />
          <Route path="templates" element={<Templates />} />
          <Route path="saved-searches" element={<SavedSearches />} />
        </Route>

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ErrorBoundary>
  )
}

export default App

