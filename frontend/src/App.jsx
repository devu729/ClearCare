import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/AuthContext'
import ProtectedRoute     from './components/ProtectedRoute'
import Login              from './pages/Login'
import ClinicianDashboard from './pages/ClinicianDashboard'
import PatientDashboard   from './pages/PatientDashboard'
import './index.css'

function RootRedirect() {
  const { user, role, loading } = useAuth()
  if (loading) return null
  if (!user)   return <Navigate to="/login" replace />
  return <Navigate to={role === 'clinician' ? '/clinician' : '/patient'} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/"          element={<RootRedirect />} />
          <Route path="/login"     element={<Login />} />
          <Route path="/clinician" element={
            <ProtectedRoute requiredRole="clinician"><ClinicianDashboard /></ProtectedRoute>
          } />
          <Route path="/patient"   element={
            <ProtectedRoute requiredRole="patient"><PatientDashboard /></ProtectedRoute>
          } />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
