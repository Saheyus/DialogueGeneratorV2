/**
 * Composant Header avec authentification et barre de recherche.
 */
import { useAuthStore } from '../../store/authStore'
import { useCommandPalette } from '../../hooks/useCommandPalette'
import { theme } from '../../theme'

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const commandPalette = useCommandPalette()

  const handleLogout = async () => {
    await logout()
  }

  const handleSearchClick = () => {
    commandPalette.open()
  }

  return (
    <header style={{ 
      padding: '0.4rem 1rem', 
      borderBottom: `1px solid ${theme.border.primary}`, 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      backgroundColor: theme.background.secondary,
      gap: '1rem',
      position: 'relative',
    }}>
      {/* Section gauche : Titre */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
        <h1 style={{ margin: 0, color: theme.text.primary, fontSize: '1.25rem', fontWeight: 600, whiteSpace: 'nowrap' }}>DialogueGenerator</h1>
        <span style={{ 
          fontSize: '2rem', 
          fontWeight: 'bold', 
          color: 'red', 
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
          marginLeft: '1rem'
        }}>
        </span>
        <span 
          title={`Date de compilation: ${new Date(__BUILD_DATE__).toLocaleString('fr-FR')}`}
          style={{ 
            color: theme.text.secondary, 
            fontSize: '0.75rem',
            whiteSpace: 'nowrap',
            fontFamily: 'monospace',
          }}
        >
          Build: {new Date(__BUILD_DATE__).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      
      {/* Section centrale : Barre de recherche */}
      {isAuthenticated && (
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', maxWidth: '600px', margin: '0 auto' }}>
          <div
            onClick={handleSearchClick}
            style={{
              width: '100%',
              maxWidth: '500px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 0.75rem',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              cursor: 'text',
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = theme.border.focus
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = theme.border.primary
            }}
          >
            <span style={{ color: theme.text.secondary, fontSize: '0.875rem' }}>🔍</span>
            <span style={{ 
              flex: 1, 
              color: theme.text.secondary, 
              fontSize: '0.875rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              Rechercher des actions, personnages, lieux...
            </span>
            <kbd style={{
              padding: '0.125rem 0.375rem',
              fontSize: '0.75rem',
              backgroundColor: theme.background.tertiary,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '3px',
              color: theme.text.secondary,
              fontFamily: 'monospace',
            }}>
              Ctrl+K
            </kbd>
          </div>
        </div>
      )}
      
      {/* Section droite : Utilisateur */}
      <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
        {isAuthenticated && user ? (
          <>
            <span style={{ color: theme.text.secondary, fontSize: '0.875rem', whiteSpace: 'nowrap' }}>Connecté en tant que: {user.username}</span>
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
                whiteSpace: 'nowrap',
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

