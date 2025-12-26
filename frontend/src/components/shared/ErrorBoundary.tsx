/**
 * Error Boundary pour capturer les erreurs React et afficher un message d'erreur.
 */
import { Component, ErrorInfo, ReactNode } from 'react'
import { theme } from '../../theme'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.props.onError?.(error, errorInfo)
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div
          style={{
            padding: '2rem',
            backgroundColor: theme.state.error.background,
            color: theme.state.error.color,
            borderRadius: '4px',
            border: `1px solid ${theme.border.primary}`,
          }}
        >
          <h3 style={{ marginTop: 0 }}>Une erreur s'est produite</h3>
          <p>{this.state.error?.message || 'Une erreur inattendue est survenue'}</p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null })
              window.location.reload()
            }}
            style={{
              padding: '0.5rem 1rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              cursor: 'pointer',
              marginTop: '1rem',
            }}
          >
            Recharger la page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

