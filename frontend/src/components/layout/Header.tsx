/**
 * Composant Header avec authentification.
 */
import { useAuthStore } from '../../store/authStore'
import { theme } from '../../theme'

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
  }

  return (
    <header style={{ 
      padding: '0.4rem 1rem', 
      borderBottom: `1px solid ${theme.border.primary}`, 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      backgroundColor: theme.background.secondary,
    }}>
      <h1 style={{ margin: 0, color: theme.text.primary, fontSize: '1.25rem', fontWeight: 600 }}>DialogueGenerator</h1>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {isAuthenticated && user ? (
          <>
            <span style={{ color: theme.text.secondary, fontSize: '0.875rem' }}>Connecté en tant que: {user.username}</span>
            <button 
              onClick={handleLogout} 
              style={{ 
                padding: '0.35rem 0.75rem',
                fontSize: '0.875rem',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                border: `1px solid ${theme.button.default.border}`,
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Déconnexion
            </button>
          </>
        ) : (
          <span style={{ color: theme.text.secondary, fontSize: '0.875rem' }}>Non connecté</span>
        )}
      </div>
    </header>
  )
}

