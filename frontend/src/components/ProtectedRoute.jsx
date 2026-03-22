import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'

export default function ProtectedRoute({ children, requiredRole }) {
  const { user, role, loading } = useAuth()

  if (loading) return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: '#f0f9ff',
      fontFamily: 'Outfit, sans-serif', color: '#0ea5e9',
      fontSize: 15, gap: 12,
    }}>
      <div style={{
        width: 20, height: 20, border: '2px solid #bae6fd',
        borderTopColor: '#0ea5e9', borderRadius: '50%',
        animation: 'spin 0.7s linear infinite',
      }} />
      Verifying access...
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )

  if (!user) return <Navigate to="/login" replace />
  if (requiredRole && role !== requiredRole)
    return <Navigate to={role === 'clinician' ? '/clinician' : '/patient'} replace />

  return children
}
