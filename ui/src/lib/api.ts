import type { QueryResponse, StreamEvent } from './types'

const BASE = '/api'

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`)
  return res.json()
}

export async function sendQuery(
  query: string,
  threadId?: string,
  hitl = false,
): Promise<QueryResponse> {
  const params = hitl ? '?hitl=true' : ''
  const res = await fetch(`${BASE}/query${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, thread_id: threadId }),
  })
  if (!res.ok) throw new Error(`Query failed: ${res.status}`)
  return res.json()
}

export async function streamQuery(
  query: string,
  threadId?: string,
  onEvent?: (event: StreamEvent) => void,
): Promise<QueryResponse> {
  const res = await fetch(`${BASE}/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, thread_id: threadId }),
  })
  if (!res.ok) throw new Error(`Stream failed: ${res.status}`)

  const reader = res.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let lastDoneData: QueryResponse | null = null

  if (reader) {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ') && currentEvent) {
          try {
            const data = JSON.parse(line.slice(6))
            const evt: StreamEvent = { event: currentEvent as StreamEvent['event'], ...data }
            onEvent?.(evt)
            if (currentEvent === 'done') {
              lastDoneData = data as QueryResponse
            }
          } catch { /* skip malformed */ }
          currentEvent = ''
        }
      }
    }
  }

  if (lastDoneData) return lastDoneData
  throw new Error('Stream ended without done event')
}

export async function approvePlan(
  threadId: string,
  plan?: string[],
): Promise<QueryResponse> {
  const res = await fetch(`${BASE}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thread_id: threadId, plan }),
  })
  if (!res.ok) throw new Error(`Approve failed: ${res.status}`)
  return res.json()
}
