import { BarChart3 } from 'lucide-react'

const EXAMPLE_CARDS = [
  { label: 'ROI by channel', icon: '📊' },
  { label: 'Find anomalies', icon: '🔍' },
  { label: 'AI marketing trends', icon: '📈' },
  { label: 'Budget optimization', icon: '💰' },
]

interface WelcomeStateProps {
  onExampleClick: (query: string) => void
}

export default function WelcomeState({ onExampleClick }: WelcomeStateProps) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4" data-testid="welcome-state">
      <BarChart3 size={36} className="text-text-muted opacity-40 mb-3" />
      <p className="text-sm font-medium text-text-secondary mb-1">
        Ask about your marketing data
      </p>
      <p className="text-xs text-text-muted max-w-[380px] text-center leading-relaxed mb-6">
        Queries are routed to analytics, research, or both.
        You approve the plan before execution.
      </p>
      <div className="grid grid-cols-2 gap-2 max-w-[360px] w-full">
        {EXAMPLE_CARDS.map((card) => (
          <button
            key={card.label}
            onClick={() => onExampleClick(card.label)}
            className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-border hover:border-primary-lighter hover:bg-primary-lighter/30 text-xs text-text-secondary transition-all cursor-pointer text-left"
          >
            <span>{card.icon}</span>
            <span>{card.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
