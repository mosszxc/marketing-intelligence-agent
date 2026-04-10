import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import WelcomeState from '../WelcomeState'

describe('WelcomeState', () => {
  it('renders welcome text', () => {
    render(<WelcomeState onExampleClick={vi.fn()} />)
    expect(screen.getByText('Ask about your marketing data')).toBeInTheDocument()
    expect(screen.getByTestId('welcome-state')).toBeInTheDocument()
  })

  it('renders example cards', () => {
    render(<WelcomeState onExampleClick={vi.fn()} />)
    expect(screen.getByText('ROI by channel')).toBeInTheDocument()
    expect(screen.getByText('Find anomalies')).toBeInTheDocument()
  })
})
