import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { LoginForm } from './components/auth/LoginForm'
import { Dashboard } from './components/layout/Dashboard'
import { InteractionsPage } from './components/interactions/InteractionsPage'
import { InteractionDetails } from './components/interactions/InteractionDetails'
import { useAuthStore } from './store/authStore'
import { ToastContainer } from './components/shared'
import './App.css'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, initialize } = useAuthStore()

  useEffect(() => {
    // Initialiser la session au démarrage (vérifie le token dans localStorage)
    initialize()
  }, [initialize])

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#1a1a1a',
        color: 'rgba(255, 255, 255, 0.87)',
      }}>
        <div>Chargement...</div>
      </div>
    )
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function InteractionDetailRoute() {
  const { id } = useParams<{ id: string }>()
  return <InteractionDetails interactionId={id || null} onClose={() => window.history.back()} />
}

function App() {
  return (
    <>
      <ToastContainer />
      <BrowserRouter>
        <Routes>
        <Route
          path="/login"
          element={
            <MainLayout fullWidth>
              <LoginForm />
            </MainLayout>
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interactions"
          element={
            <ProtectedRoute>
              <MainLayout>
                <InteractionsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interactions/:id"
          element={
            <ProtectedRoute>
              <MainLayout fullWidth>
                <InteractionDetailRoute />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
    </>
  )
}

export default App

