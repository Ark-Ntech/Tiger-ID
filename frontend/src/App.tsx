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
import Investigation2 from './pages/Investigation2'
import Tigers from './pages/Tigers'
import TigerDetail from './pages/TigerDetail'
import Facilities from './pages/Facilities'
import FacilityDetail from './pages/FacilityDetail'
import ModelWeights from './pages/ModelWeights'
import FineTuning from './pages/FineTuning'
import DatasetManagement from './pages/DatasetManagement'
import Verification from './pages/Verification'
import PasswordReset from './pages/PasswordReset'
import SearchResults from './pages/SearchResults'
import NotFound from './pages/NotFound'

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
          <Route path="investigations/launch" element={<Navigate to="/investigations?tab=1" replace />} />
          <Route path="investigation2" element={<Investigation2 />} />
          <Route path="tigers" element={<Tigers />} />
          <Route path="tigers/:id" element={<TigerDetail />} />
          <Route path="facilities" element={<Facilities />} />
          <Route path="facilities/:id" element={<FacilityDetail />} />
          <Route path="model-weights" element={<ModelWeights />} />
          <Route path="finetuning" element={<FineTuning />} />
          <Route path="dataset-management" element={<DatasetManagement />} />
          <Route path="verification" element={<Verification />} />
          {/* Redirect obsolete routes to consolidated pages */}
          <Route path="tools" element={<Navigate to="/investigations/launch" replace />} />
          <Route path="model-testing" element={<Navigate to="/investigations/launch" replace />} />
          <Route path="model-dashboard" element={<Navigate to="/dashboard" replace />} />
          <Route path="templates" element={<Navigate to="/investigations" replace />} />
          <Route path="saved-searches" element={<Navigate to="/investigations" replace />} />
          <Route path="search" element={<SearchResults />} />
        </Route>

        {/* Catch all - 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ErrorBoundary>
  )
}

export default App

