import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ChatMessage from '../ChatMessage'

describe('ChatMessage', () => {
  it('renders user message', () => {
    render(
      <ChatMessage
        message={{ id: '1', role: 'user', content: 'Hello world' }}
      />,
    )
    expect(screen.getByText('Hello world')).toBeInTheDocument()
    expect(screen.getByTestId('chat-message-user')).toBeInTheDocument()
  })

  it('renders assistant markdown', () => {
    render(
      <ChatMessage
        message={{ id: '2', role: 'assistant', content: '**Bold text** and `code`' }}
      />,
    )
    expect(screen.getByText('Bold text')).toBeInTheDocument()
    expect(screen.getByText('code')).toBeInTheDocument()
    expect(screen.getByTestId('chat-message-assistant')).toBeInTheDocument()
  })

  it('renders plan caption', () => {
    render(
      <ChatMessage
        message={{ id: '3', role: 'assistant', content: 'Result', plan: ['analytics', 'research'] }}
      />,
    )
    expect(screen.getByText('agents: analytics, research')).toBeInTheDocument()
  })

  it('renders sources', () => {
    render(
      <ChatMessage
        message={{
          id: '4',
          role: 'assistant',
          content: 'Result',
          sources: [{ title: 'Source 1', url: 'https://example.com', snippet: '' }],
        }}
      />,
    )
    expect(screen.getByText('Source 1')).toBeInTheDocument()
  })
})
