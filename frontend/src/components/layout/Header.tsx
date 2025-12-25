/**
 * Composant Header avec authentification.
 */
import { useAuthStore } from '../../store/authStore'

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
  }

  return (
    <header style={{ padding: '1rem', borderBottom: '1px solid #ccc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <h1>DialogueGenerator</h1>
      <div>
        {isAuthenticated && user ? (
          <>
            <span>Connecté en tant que: {user.username}</span>
            <button onClick={handleLogout} style={{ marginLeft: '1rem' }}>
              Déconnexion
            </button>
          </>
        ) : (
          <span>Non connecté</span>
        )}
      </div>
    </header>
  )
}

