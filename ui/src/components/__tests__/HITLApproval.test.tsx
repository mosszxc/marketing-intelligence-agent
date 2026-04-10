import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import HITLApproval from '../HITLApproval'

describe('HITLApproval', () => {
  it('shows plan and approve button', () => {
    render(
      <HITLApproval plan={['analytics', 'research']} onApprove={vi.fn()} />,
    )
    expect(screen.getByText('analytics, research')).toBeInTheDocument()
    expect(screen.getByTestId('approve-button')).toBeInTheDocument()
  })

  it('calls onApprove without plan on Approve click', () => {
    const handler = vi.fn()
    render(
      <HITLApproval plan={['analytics', 'research']} onApprove={handler} />,
    )
    fireEvent.click(screen.getByTestId('approve-button'))
    expect(handler).toHaveBeenCalledWith()
  })

  it('calls onApprove with analytics only', () => {
    const handler = vi.fn()
    render(
      <HITLApproval plan={['analytics', 'research']} onApprove={handler} />,
    )
    fireEvent.click(screen.getByText('Analytics only'))
    expect(handler).toHaveBeenCalledWith(['analytics'])
  })
})
