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
      padding: '1rem', 
      borderBottom: `1px solid ${theme.border.primary}`, 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      backgroundColor: theme.background.secondary,
    }}>
      <h1 style={{ margin: 0, color: theme.text.primary }}>DialogueGenerator</h1>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {isAuthenticated && user ? (
          <>
            <span style={{ color: theme.text.secondary }}>Connecté en tant que: {user.username}</span>
            <button 
              onClick={handleLogout} 
              style={{ 
                marginLeft: '1rem',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                border: `1px solid ${theme.button.default.border}`,
              }}
            >
              Déconnexion
            </button>
          </>
        ) : (
          <span style={{ color: theme.text.secondary }}>Non connecté</span>
        )}
      </div>
    </header>
  )
}

