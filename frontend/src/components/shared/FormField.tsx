/**
 * Wrapper pour champs de formulaire avec label/error.
 */
import { ReactNode } from 'react'
import { theme } from '../../theme'

export interface FormFieldProps {
  label: string
  error?: string
  required?: boolean
  children: ReactNode
  style?: React.CSSProperties
  htmlFor?: string
}

export function FormField({
  label,
  error,
  required = false,
  children,
  style,
  htmlFor,
}: FormFieldProps) {
  return (
    <div
      style={{
        marginBottom: '1rem',
        ...style,
      }}
    >
      <label
        htmlFor={htmlFor}
        style={{
          display: 'block',
          marginBottom: '0.5rem',
          color: theme.text.primary,
          fontSize: '0.9rem',
          fontWeight: 500,
        }}
      >
        {label}
        {required && (
          <span style={{ color: theme.state.error.color, marginLeft: '0.25rem' }}>
            *
          </span>
        )}
      </label>
      {children}
      {error && (
        <div
          style={{
            marginTop: '0.25rem',
            fontSize: '0.85rem',
            color: theme.state.error.color,
          }}
        >
          {error}
        </div>
      )}
    </div>
  )
}



