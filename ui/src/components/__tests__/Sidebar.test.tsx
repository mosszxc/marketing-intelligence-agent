import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Sidebar from '../Sidebar'

describe('Sidebar', () => {
  it('shows example queries', () => {
    render(
      <Sidebar
        threadId="test-1234-5678"
        onNewConversation={vi.fn()}
        onExampleClick={vi.fn()}
      />,
    )
    expect(screen.getByText('ROI by channel')).toBeInTheDocument()
    expect(screen.getByText('Anomalies in spend?')).toBeInTheDocument()
    expect(screen.getByText('AI marketing trends 2026')).toBeInTheDocument()
  })

  it('calls onExampleClick when example clicked', () => {
    const handler = vi.fn()
    render(
      <Sidebar
        threadId="test-1234-5678"
        onNewConversation={vi.fn()}
        onExampleClick={handler}
      />,
    )
    fireEvent.click(screen.getByText('ROI by channel'))
    expect(handler).toHaveBeenCalledWith('ROI by channel')
  })

  it('shows CSV upload button', () => {
    render(
      <Sidebar
        threadId="test-1234-5678"
        onNewConversation={vi.fn()}
        onExampleClick={vi.fn()}
      />,
    )
    expect(screen.getByTestId('csv-upload-button')).toBeInTheDocument()
    expect(screen.getByText('Upload CSV')).toBeInTheDocument()
  })

  it('shows thread id snippet', () => {
    render(
      <Sidebar
        threadId="abcdef12-3456-7890"
        onNewConversation={vi.fn()}
        onExampleClick={vi.fn()}
      />,
    )
    expect(screen.getByText('thread abcdef12')).toBeInTheDocument()
  })
})
