/**
 * Système de toast notifications.
 */
import { useState, useCallback, useEffect } from 'react'
import { theme } from '../../theme'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: string
  message: string
  type: ToastType
  duration?: number
}

interface ToastProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastComponent({ toast, onRemove }: ToastProps) {
  useEffect(() => {
    const duration = toast.duration ?? 5000
    const timer = setTimeout(() => {
      onRemove(toast.id)
    }, duration)

    return () => clearTimeout(timer)
  }, [toast, onRemove])

  const getStyles = () => {
    const baseStyles: React.CSSProperties = {
      padding: '0.75rem 1rem',
      borderRadius: '4px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
      marginBottom: '0.5rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      minWidth: '300px',
      maxWidth: '500px',
      animation: 'slideIn 0.3s ease-out',
    }

    switch (toast.type) {
      case 'success':
        return {
          ...baseStyles,
          backgroundColor: theme.state.success.background,
          color: theme.state.success.color,
          borderLeft: `4px solid ${theme.state.success.color}`,
        }
      case 'error':
        return {
          ...baseStyles,
          backgroundColor: theme.state.error.background,
          color: theme.state.error.color,
          borderLeft: `4px solid ${theme.state.error.border}`,
        }
      case 'warning':
        return {
          ...baseStyles,
          backgroundColor: '#3a3a1a',
          color: '#ffd43b',
          borderLeft: '4px solid #ffd43b',
        }
      case 'info':
      default:
        return {
          ...baseStyles,
          backgroundColor: theme.state.info.background,
          color: theme.state.info.color,
          borderLeft: `4px solid ${theme.state.info.color}`,
        }
    }
  }

  return (
    <div style={getStyles()}>
      <span>{toast.message}</span>
      <button
        onClick={() => onRemove(toast.id)}
        style={{
          background: 'none',
          border: 'none',
          color: 'inherit',
          cursor: 'pointer',
          fontSize: '1.2rem',
          lineHeight: 1,
          marginLeft: '1rem',
          opacity: 0.7,
          padding: 0,
        }}
        aria-label="Fermer"
      >
        ×
      </button>
    </div>
  )
}

let toastIdCounter = 0

class ToastManager {
  private listeners: Set<(toasts: Toast[]) => void> = new Set()
  private toasts: Toast[] = []

  subscribe(listener: (toasts: Toast[]) => void) {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notify() {
    this.listeners.forEach((listener) => listener([...this.toasts]))
  }

  show(message: string, type: ToastType = 'info', duration?: number) {
    const toast: Toast = {
      id: `toast-${toastIdCounter++}`,
      message,
      type,
      duration,
    }
    this.toasts.push(toast)
    this.notify()
    return toast.id
  }

  remove(id: string) {
    this.toasts = this.toasts.filter((t) => t.id !== id)
    this.notify()
  }

  clear() {
    this.toasts = []
    this.notify()
  }

  getToasts(): Toast[] {
    return [...this.toasts]
  }
}

export const toastManager = new ToastManager()

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    const unsubscribe = toastManager.subscribe(setToasts)
    return unsubscribe
  }, [])

  const handleRemove = useCallback((id: string) => {
    toastManager.remove(id)
  }, [])

  if (toasts.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        zIndex: 10000,
        pointerEvents: 'none',
      }}
    >
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>
      <div style={{ pointerEvents: 'auto' }}>
        {toasts.map((toast) => (
          <ToastComponent key={toast.id} toast={toast} onRemove={handleRemove} />
        ))}
      </div>
    </div>
  )
}

// Hook pour utiliser les toasts facilement
export function useToast() {
  return useCallback(
    (message: string, type: ToastType = 'info', duration?: number): string => {
      return toastManager.show(message, type, duration)
    },
    []
  )
}

