/**
 * Layout principal de l'application.
 */
import { Header } from './Header'
import { ReactNode } from 'react'

interface MainLayoutProps {
  children: ReactNode
  fullWidth?: boolean
}

export function MainLayout({ children, fullWidth = false }: MainLayoutProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header />
      <main style={{ flex: 1, overflow: 'hidden', ...(fullWidth ? { padding: '2rem' } : {}) }}>
        {children}
      </main>
    </div>
  )
}

