export interface SourceItem {
  title: string
  url: string
  snippet: string
}

export interface QueryResponse {
  thread_id: string
  plan: string[]
  final_answer: string
  charts: string[]
  sources: SourceItem[]
  awaiting_approval: boolean
}

export interface StreamEvent {
  event: 'node_end' | 'done' | 'error'
  node?: string
  data?: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  charts?: string[]
  sources?: SourceItem[]
  plan?: string[]
}
