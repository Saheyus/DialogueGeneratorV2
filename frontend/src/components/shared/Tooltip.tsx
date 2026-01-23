/**
 * Composant Tooltip réutilisable pour afficher des informations contextuelles.
 */
import { useState, useRef, useEffect, useCallback, ReactNode } from 'react'
import { theme } from '../../theme'

export interface TooltipProps {
  /**
   * Contenu à afficher dans le tooltip.
   */
  content: ReactNode
  /**
   * Élément enfant qui déclenchera l'affichage du tooltip au survol.
   */
  children: ReactNode
  /**
   * Position du tooltip par rapport à l'élément.
   * @default 'top'
   */
  position?: 'top' | 'bottom' | 'left' | 'right'
  /**
   * Délai avant l'affichage du tooltip (en ms).
   * @default 300
   */
  delay?: number
  /**
   * Largeur maximale du tooltip.
   * @default '300px'
   */
  maxWidth?: string
}

/**
 * Composant Tooltip qui affiche un contenu informatif au survol d'un élément.
 */
export function Tooltip({
  content,
  children,
  position = 'top',
  delay = 300,
  maxWidth = '300px',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 })
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const updateTooltipPosition = useCallback(() => {
    if (triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect()
      const tooltipRect = tooltipRef.current.getBoundingClientRect()
      const scrollX = window.scrollX || window.pageXOffset
      const scrollY = window.scrollY || window.pageYOffset

      let top = 0
      let left = 0

      switch (position) {
        case 'top':
          top = triggerRect.top + scrollY - tooltipRect.height - 8
          left = triggerRect.left + scrollX + triggerRect.width / 2 - tooltipRect.width / 2
          break
        case 'bottom':
          top = triggerRect.bottom + scrollY + 8
          left = triggerRect.left + scrollX + triggerRect.width / 2 - tooltipRect.width / 2
          break
        case 'left':
          top = triggerRect.top + scrollY + triggerRect.height / 2 - tooltipRect.height / 2
          left = triggerRect.left + scrollX - tooltipRect.width - 8
          break
        case 'right':
          top = triggerRect.top + scrollY + triggerRect.height / 2 - tooltipRect.height / 2
          left = triggerRect.right + scrollX + 8
          break
      }

      // Ajuster si le tooltip sort de l'écran
      const padding = 8
      if (left < padding) left = padding
      if (left + tooltipRect.width > window.innerWidth - padding) {
        left = window.innerWidth - tooltipRect.width - padding
      }
      if (top < padding) top = padding
      if (top + tooltipRect.height > window.innerHeight + scrollY - padding) {
        top = window.innerHeight + scrollY - tooltipRect.height - padding
      }

      setTooltipPosition({ top, left })
    }
  }, [position])

  const showTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
      // Utiliser requestAnimationFrame pour s'assurer que le DOM est mis à jour
      requestAnimationFrame(() => {
        updateTooltipPosition()
      })
    }, delay)
  }

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    setIsVisible(false)
  }

  // Mettre à jour la position quand le tooltip devient visible
  useEffect(() => {
    if (isVisible) {
      updateTooltipPosition()
      const handleResize = () => updateTooltipPosition()
      const handleScroll = () => updateTooltipPosition()
      window.addEventListener('resize', handleResize)
      window.addEventListener('scroll', handleScroll, true)
      return () => {
        window.removeEventListener('resize', handleResize)
        window.removeEventListener('scroll', handleScroll, true)
      }
    }
  }, [isVisible, updateTooltipPosition])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        style={{ display: 'inline-block' }}
      >
        {children}
      </div>
      {isVisible && (
        <div
          ref={tooltipRef}
          style={{
            position: 'absolute',
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            backgroundColor: theme.background.panel,
            color: theme.text.primary,
            padding: '0.75rem',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
            zIndex: 10000,
            maxWidth,
            fontSize: '0.875rem',
            lineHeight: '1.5',
            border: `1px solid ${theme.border.primary}`,
            pointerEvents: 'none',
          }}
        >
          {content}
        </div>
      )}
    </>
  )
}

/**
 * Composant InfoIcon qui affiche une icône d'information avec un tooltip.
 */
export interface InfoIconProps {
  /**
   * Contenu du tooltip.
   */
  content: ReactNode
  /**
   * Position du tooltip.
   * @default 'top'
   */
  position?: 'top' | 'bottom' | 'left' | 'right'
}

export function InfoIcon({ content, position = 'top' }: InfoIconProps) {
  return (
    <Tooltip content={content} position={position}>
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '18px',
          height: '18px',
          borderRadius: '50%',
          backgroundColor: theme.background.secondary,
          color: theme.text.secondary,
          fontSize: '12px',
          cursor: 'help',
          border: `1px solid ${theme.border.primary}`,
          marginLeft: '0.5rem',
          verticalAlign: 'middle',
        }}
      >
        ⓘ
      </span>
    </Tooltip>
  )
}

