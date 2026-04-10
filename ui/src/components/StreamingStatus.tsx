import { Loader2 } from 'lucide-react'

const NODE_LABELS: Record<string, string> = {
  supervisor: 'Supervisor — classifying',
  analytics: 'Analytics — processing',
  research: 'Research — searching',
  synthesize: 'Report — building',
}

interface StreamingStatusProps {
  activeNodes: string[]
  isStreaming: boolean
}

export default function StreamingStatus({ activeNodes, isStreaming }: StreamingStatusProps) {
  if (!isStreaming && activeNodes.length === 0) return null

  return (
    <div
      className="rounded-lg border border-border bg-surface px-4 py-3 mb-2"
      data-testid="streaming-status"
    >
      <div className="flex items-center gap-2 mb-2">
        {isStreaming && <Loader2 size={14} className="text-primary-light animate-spin" />}
        <span className="text-xs font-semibold text-text-secondary">
          {isStreaming ? 'Processing...' : 'Done'}
        </span>
      </div>
      <div className="space-y-1">
        {activeNodes.map((node) => (
          <p key={node} className="font-mono text-xs text-text-secondary">
            {NODE_LABELS[node] || node} ✓
          </p>
        ))}
      </div>
    </div>
  )
}
