import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { LoginForm } from './components/auth/LoginForm'
import { Dashboard } from './components/layout/Dashboard'
import { UnityDialoguesPage } from './components/unityDialogues/UnityDialoguesPage'
import { UsageDashboard } from './components/usage/UsageDashboard'
import { useAuthStore } from './store/authStore'
import { ToastContainer } from './components/shared'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'
import './App.css'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, initialize } = useAuthStore()

  useEffect(() => {
    // Initialiser la session au démarrage (vérifie le token dans localStorage)
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'App.tsx:17',message:'ProtectedRoute useEffect: calling initialize',data:{isLoading,isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'D'})}).catch(()=>{});
    // #endregion
    console.log('[ProtectedRoute] Initialisation...')
    initialize().then(() => {
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'App.tsx:21',message:'ProtectedRoute: initialize() resolved',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'A,B'})}).catch(()=>{});
      // #endregion
      console.log('[ProtectedRoute] Initialisation terminée')
    }).catch((error) => {
      // #region agent log
      fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'App.tsx:25',message:'ProtectedRoute: initialize() rejected',data:{error:error?.toString(),timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'E'})}).catch(()=>{});
      // #endregion
      console.error('[ProtectedRoute] Erreur lors de l\'initialisation:', error)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Exécuter une seule fois au montage

  // Log pour debug
  useEffect(() => {
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'App.tsx:31',message:'ProtectedRoute: state changed (render)',data:{isLoading,isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'C'})}).catch(()=>{});
    // #endregion
    console.log('[ProtectedRoute] State changé:', { isLoading, isAuthenticated })
  }, [isLoading, isAuthenticated])

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

/**
 * Composant pour gérer les raccourcis de navigation globaux.
 */
function NavigationShortcuts() {
  const navigate = useNavigate()
  const location = useLocation()

  useKeyboardShortcuts(
    [
      {
        key: 'ctrl+1',
        handler: () => {
          if (location.pathname !== '/') {
            navigate('/')
          }
        },
        description: 'Naviguer vers Dashboard',
      },
      {
        key: 'ctrl+2',
        handler: () => {
          if (location.pathname !== '/unity-dialogues') {
            navigate('/unity-dialogues')
          }
        },
        description: 'Naviguer vers Dialogues Unity',
      },
      {
        key: 'ctrl+3',
        handler: () => {
          if (location.pathname !== '/usage') {
            navigate('/usage')
          }
        },
        description: 'Naviguer vers Usage/Statistiques',
      },
    ],
    [navigate, location.pathname]
  )

  return null
}

function AppRoutes() {
  return (
    <>
      <NavigationShortcuts />
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
          path="/unity-dialogues"
          element={
            <ProtectedRoute>
              <MainLayout>
                <UnityDialoguesPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/usage"
          element={
            <ProtectedRoute>
              <MainLayout>
                <UsageDashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

function App() {
  return (
    <>
      <ToastContainer />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </>
  )
}

export default App

