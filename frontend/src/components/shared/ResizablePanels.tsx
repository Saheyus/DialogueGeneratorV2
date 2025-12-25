/**
 * Composant pour créer des panneaux redimensionnables avec localStorage.
 */
import { useState, useEffect, useRef, useCallback, ReactNode } from 'react'
import { theme } from '../../theme'

interface ResizablePanelsProps {
  children: ReactNode[]
  storageKey?: string
  defaultSizes?: number[]
  minSizes?: number[]
  direction?: 'horizontal' | 'vertical'
  style?: React.CSSProperties
}

export function ResizablePanels({
  children,
  storageKey,
  defaultSizes = children.map(() => 1),
  minSizes = children.map(() => 100),
  direction = 'horizontal',
  style,
}: ResizablePanelsProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [sizes, setSizes] = useState<number[]>(() => {
    if (storageKey) {
      try {
        const stored = localStorage.getItem(`resizable_${storageKey}`)
        if (stored) {
          const parsed = JSON.parse(stored)
          if (Array.isArray(parsed) && parsed.length === children.length) {
            return parsed
          }
        }
      } catch {
        // Ignore errors
      }
    }
    return defaultSizes
  })

  const [isDragging, setIsDragging] = useState<number | null>(null)
  const [startPos, setStartPos] = useState(0)
  const [startSizes, setStartSizes] = useState<number[]>([])

  useEffect(() => {
    if (storageKey && sizes) {
      try {
        localStorage.setItem(`resizable_${storageKey}`, JSON.stringify(sizes))
      } catch {
        // Ignore storage errors
      }
    }
  }, [sizes, storageKey])

  const normalizeSizes = useCallback(
    (newSizes: number[]): number[] => {
      const total = newSizes.reduce((sum, size) => sum + size, 0)
      return newSizes.map((size) => (size / total) * 100)
    },
    []
  )

  const handleMouseDown = useCallback(
    (index: number, e: React.MouseEvent) => {
      e.preventDefault()
      setIsDragging(index)
      const pos = direction === 'horizontal' ? e.clientX : e.clientY
      setStartPos(pos)
      setStartSizes([...sizes])
    },
    [direction, sizes]
  )

  useEffect(() => {
    if (isDragging === null || !containerRef.current) return

    const handleMouseMove = (e: MouseEvent) => {
      const pos = direction === 'horizontal' ? e.clientX : e.clientY
      const delta = pos - startPos
      const containerSize =
        direction === 'horizontal'
          ? containerRef.current!.clientWidth
          : containerRef.current!.clientHeight

      const deltaPercent = (delta / containerSize) * 100

      const newSizes = [...startSizes]
      const leftSize = newSizes[isDragging]
      const rightSize = newSizes[isDragging + 1]

      const leftMin = (minSizes[isDragging] / containerSize) * 100
      const rightMin = (minSizes[isDragging + 1] / containerSize) * 100

      const newLeftSize = Math.max(
        leftMin,
        Math.min(leftSize + deltaPercent, 100 - rightMin)
      )
      const newRightSize = Math.max(
        rightMin,
        Math.min(rightSize - deltaPercent, 100 - leftMin)
      )

      newSizes[isDragging] = newLeftSize
      newSizes[isDragging + 1] = newRightSize

      setSizes(normalizeSizes(newSizes))
    }

    const handleMouseUp = () => {
      setIsDragging(null)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, startPos, startSizes, direction, minSizes, normalizeSizes])

  const isHorizontal = direction === 'horizontal'

  return (
    <div
      ref={containerRef}
      style={{
        display: 'flex',
        flexDirection: isHorizontal ? 'row' : 'column',
        height: '100%',
        width: '100%',
        overflow: 'hidden',
        position: 'relative',
        ...style,
      }}
    >
      {children.map((child, index) => (
        <div key={index}>
          <div
            style={{
              width: isHorizontal ? `${sizes[index]}%` : '100%',
              height: isHorizontal ? '100%' : `${sizes[index]}%`,
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            {child}
          </div>
          {index < children.length - 1 && (
            <div
              onMouseDown={(e) => handleMouseDown(index, e)}
              style={{
                [isHorizontal ? 'width' : 'height']: '4px',
                [isHorizontal ? 'height' : 'width']: '100%',
                backgroundColor: isDragging === index
                  ? theme.button.primary.background
                  : theme.border.primary,
                cursor: isHorizontal ? 'col-resize' : 'row-resize',
                position: 'relative',
                zIndex: 10,
                flexShrink: 0,
                transition: isDragging === index ? 'none' : 'background-color 0.2s',
              }}
            />
          )}
        </div>
      ))}
    </div>
  )
}

