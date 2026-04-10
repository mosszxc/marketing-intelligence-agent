import { useCallback, useRef, useState } from 'react'
import { v4 as uuidv4 } from 'uuid'

import Sidebar from './components/Sidebar'
import WelcomeState from './components/WelcomeState'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import HITLApproval from './components/HITLApproval'
import StreamingStatus from './components/StreamingStatus'
import { sendQuery, approvePlan } from './lib/api'
import type { ChatMessage as ChatMessageType } from './lib/types'

function generateId() {
  return Math.random().toString(36).slice(2, 10)
}

function generateThreadId() {
  // Use uuid if available, fallback to random
  try {
    return uuidv4()
  } catch {
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`
  }
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [threadId, setThreadId] = useState(generateThreadId)
  const [isLoading, setIsLoading] = useState(false)
  const [streamNodes, setStreamNodes] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [hitlPlan, setHitlPlan] = useState<string[] | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendQuery = useCallback(async (query: string) => {
    // Add user message
    const userMsg: ChatMessageType = {
      id: generateId(),
      role: 'user',
      content: query,
    }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)
    setStreamNodes([])
    setIsStreaming(true)
    setTimeout(scrollToBottom, 50)

    try {
      const result = await sendQuery(query, threadId, true)
      setStreamNodes(result.plan)
      setIsStreaming(false)

      if (result.awaiting_approval) {
        setHitlPlan(result.plan)
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'assistant',
            content: `Plan: **${result.plan.join(', ')}** — awaiting approval.`,
            plan: result.plan,
          },
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'assistant',
            content: result.final_answer,
            charts: result.charts,
            sources: result.sources,
            plan: result.plan,
          },
        ])
      }
    } catch (err) {
      setIsStreaming(false)
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        },
      ])
    } finally {
      setIsLoading(false)
      setTimeout(scrollToBottom, 50)
    }
  }, [threadId])

  const handleApprove = useCallback(async (plan?: string[]) => {
    setIsLoading(true)
    setHitlPlan(null)
    setStreamNodes([])
    setIsStreaming(true)

    try {
      const result = await approvePlan(threadId, plan)
      setStreamNodes(result.plan)
      setIsStreaming(false)

      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: 'assistant',
          content: result.final_answer,
          charts: result.charts,
          sources: result.sources,
          plan: result.plan,
        },
      ])
    } catch (err) {
      setIsStreaming(false)
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        },
      ])
    } finally {
      setIsLoading(false)
      setTimeout(scrollToBottom, 50)
    }
  }, [threadId])

  const handleNewConversation = useCallback(() => {
    setMessages([])
    setThreadId(generateThreadId())
    setHitlPlan(null)
    setStreamNodes([])
    setIsStreaming(false)
  }, [])

  const showWelcome = messages.length === 0 && !hitlPlan

  return (
    <div className="flex h-screen">
      <Sidebar
        threadId={threadId}
        onNewConversation={handleNewConversation}
        onExampleClick={handleSendQuery}
      />

      <main className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="border-b-2 border-border px-4 py-3">
          <h1 className="text-lg font-bold tracking-tight text-text-primary">
            Marketing Intelligence Agent
          </h1>
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          <div className="max-w-[860px] mx-auto">
            {showWelcome && <WelcomeState onExampleClick={handleSendQuery} />}

            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {isStreaming && (
              <StreamingStatus activeNodes={streamNodes} isStreaming={isStreaming} />
            )}

            {hitlPlan && (
              <HITLApproval
                plan={hitlPlan}
                onApprove={handleApprove}
                disabled={isLoading}
              />
            )}

            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Input */}
        <ChatInput
          onSend={handleSendQuery}
          disabled={isLoading || !!hitlPlan}
        />
      </main>
    </div>
  )
}
