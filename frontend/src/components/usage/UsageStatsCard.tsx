/**
 * Carte de statistiques d'utilisation LLM.
 */
import './UsageStatsCard.css'

interface UsageStatsCardProps {
  title: string
  value: string | number
  unit?: string
  subtitle?: string
  className?: string
}

export function UsageStatsCard({
  title,
  value,
  unit,
  subtitle,
  className = '',
}: UsageStatsCardProps) {
  return (
    <div className={`usage-stats-card ${className}`}>
      <div className="usage-stats-card__title">{title}</div>
      <div className="usage-stats-card__value">
        {typeof value === 'number' ? value.toLocaleString() : value}
        {unit && <span className="usage-stats-card__unit">{unit}</span>}
      </div>
      {subtitle && <div className="usage-stats-card__subtitle">{subtitle}</div>}
    </div>
  )
}




