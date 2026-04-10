interface HITLApprovalProps {
  plan: string[]
  onApprove: (plan?: string[]) => void
  disabled?: boolean
}

export default function HITLApproval({ plan, onApprove, disabled }: HITLApprovalProps) {
  return (
    <div
      className="rounded-lg border border-primary-lighter border-l-4 border-l-primary bg-linear-to-br from-blue-50 to-primary-lighter/40 px-4 py-3 mb-2"
      data-testid="hitl-approval"
    >
      <p className="text-sm text-text-secondary mb-3">
        Supervisor proposed plan: <strong className="text-text-primary">{plan.join(', ')}</strong>
      </p>
      <div className="flex gap-2">
        <button
          onClick={() => onApprove()}
          disabled={disabled}
          className="px-4 py-2 rounded-md bg-primary text-white text-xs font-semibold shadow-sm hover:bg-[#1D4ED8] transition-colors disabled:opacity-50 cursor-pointer"
          data-testid="approve-button"
        >
          Approve
        </button>
        {plan.includes('analytics') && (
          <button
            onClick={() => onApprove(['analytics'])}
            disabled={disabled}
            className="px-3 py-2 rounded-md border border-border bg-surface text-text-secondary text-xs font-semibold hover:border-primary-light hover:text-primary transition-all disabled:opacity-50 cursor-pointer"
          >
            Analytics only
          </button>
        )}
        {plan.includes('research') && (
          <button
            onClick={() => onApprove(['research'])}
            disabled={disabled}
            className="px-3 py-2 rounded-md border border-border bg-surface text-text-secondary text-xs font-semibold hover:border-primary-light hover:text-primary transition-all disabled:opacity-50 cursor-pointer"
          >
            Research only
          </button>
        )}
      </div>
    </div>
  )
}
