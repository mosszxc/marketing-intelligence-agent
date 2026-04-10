import { SendHorizonal } from 'lucide-react'
import { useState, type FormEvent, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (query: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const q = value.trim()
    if (!q || disabled) return
    onSend(q)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-border bg-bg px-4 py-3"
      data-testid="chat-input"
    >
      <div className="flex items-end gap-2 max-w-[860px] mx-auto">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your marketing data..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-xl border-[1.5px] border-border bg-surface px-3 py-2.5 text-sm outline-none focus:border-primary-light focus:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] disabled:opacity-50 placeholder:text-text-muted"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="p-2.5 rounded-xl bg-primary text-white hover:bg-primary-light transition-colors disabled:opacity-30 cursor-pointer shrink-0"
        >
          <SendHorizonal size={16} />
        </button>
      </div>
    </form>
  )
}
