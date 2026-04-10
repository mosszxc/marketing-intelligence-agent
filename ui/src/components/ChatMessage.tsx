import Markdown from 'react-markdown'
import type { ChatMessage as ChatMessageType } from '../lib/types'

interface ChatMessageProps {
  message: ChatMessageType
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex gap-3 px-4 py-3 rounded-lg border shadow-xs mb-2 ${
        isUser
          ? 'bg-linear-to-br from-bg to-primary-lighter/30 border-primary-lighter'
          : 'bg-surface border-border hover:border-primary-lighter'
      }`}
      data-testid={`chat-message-${message.role}`}
    >
      {/* Avatar */}
      <div
        className={`w-7 h-7 min-w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
          isUser
            ? 'bg-primary-lighter text-primary'
            : 'bg-linear-to-br from-primary to-primary-light text-white'
        }`}
      >
        {isUser ? 'U' : 'AI'}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="prose prose-sm max-w-none text-text-secondary [&_strong]:text-text-primary [&_h1]:text-base [&_h1]:mb-2 [&_h2]:text-sm [&_h2]:text-primary [&_h2]:mt-3 [&_h2]:mb-2 [&_p]:text-[13px] [&_p]:leading-relaxed [&_li]:text-[13px] [&_li]:mb-1 [&_code]:font-mono [&_code]:text-xs [&_code]:bg-border-light [&_code]:text-primary [&_code]:px-1 [&_code]:rounded [&_table]:text-xs [&_th]:bg-bg [&_th]:px-2 [&_th]:py-1 [&_td]:px-2 [&_td]:py-1">
          <Markdown>{message.content}</Markdown>
        </div>

        {/* Charts */}
        {message.charts?.map((chart, i) => (
          <img
            key={i}
            src={`data:image/png;base64,${chart}`}
            alt={`Chart ${i + 1}`}
            className="rounded-lg border border-border shadow-sm my-2 max-w-full"
          />
        ))}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-border-light">
            <p className="text-[10px] font-mono text-text-muted mb-1">Sources</p>
            {message.sources.map((s, i) => (
              <a
                key={i}
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-xs text-primary-light hover:underline truncate"
              >
                {s.title || s.url}
              </a>
            ))}
          </div>
        )}

        {/* Plan caption */}
        {message.plan && message.plan.length > 0 && (
          <p className="mt-1 font-mono text-[10px] text-text-muted">
            agents: {message.plan.join(', ')}
          </p>
        )}
      </div>
    </div>
  )
}
