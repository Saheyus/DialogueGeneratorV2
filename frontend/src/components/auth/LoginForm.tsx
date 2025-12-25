/**
 * Formulaire de connexion.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'

export function LoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const { login, isLoading, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  // Rediriger si déjà connecté
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    try {
      await login(username, password)
      // Redirection après connexion réussie
      navigate('/', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '400px', margin: '0 auto' }}>
      <h2 style={{ color: theme.text.primary }}>Connexion</h2>
      {error && <div style={{ color: theme.state.error.color, marginBottom: '1rem' }}>{error}</div>}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary }}>
          Nom d'utilisateur:
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              marginTop: '0.5rem',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </label>
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary }}>
          Mot de passe:
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              marginTop: '0.5rem',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </label>
      </div>
      <button 
        type="submit" 
        disabled={isLoading} 
        style={{ 
          width: '100%', 
          padding: '0.75rem',
          backgroundColor: theme.button.primary.background,
          color: theme.button.primary.color,
        }}
      >
        {isLoading ? 'Connexion...' : 'Se connecter'}
      </button>
    </form>
  )
}

