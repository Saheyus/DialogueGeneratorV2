import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { LoginForm } from './components/auth/LoginForm'
import { GenerationPanel } from './components/generation/GenerationPanel'
import { useAuthStore } from './store/authStore'
import './App.css'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, fetchCurrentUser } = useAuthStore()

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      fetchCurrentUser()
    }
  }, [isAuthenticated, isLoading, fetchCurrentUser])

  if (isLoading) {
    return <div>Chargement...</div>
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<MainLayout><LoginForm /></MainLayout>} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <GenerationPanel />
              </MainLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App

