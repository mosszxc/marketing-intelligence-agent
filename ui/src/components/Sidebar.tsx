import { BarChart3, MessageSquarePlus, Upload, CheckCircle } from 'lucide-react'
import { useRef, useState } from 'react'

const EXAMPLES = [
  'ROI by channel',
  'Anomalies in spend?',
  'AI marketing trends 2026',
  'Compare ROI with benchmarks',
]

interface SidebarProps {
  threadId: string
  onNewConversation: () => void
  onExampleClick: (query: string) => void
}

export default function Sidebar({ threadId, onNewConversation, onExampleClick }: SidebarProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadStatus('Uploading...')
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      if (!res.ok) {
        const err = await res.json()
        setUploadStatus(`Error: ${err.detail}`)
        return
      }
      const data = await res.json()
      setUploadStatus(`${data.filename} — ${data.rows} rows`)
    } catch {
      setUploadStatus('Upload failed')
    }
  }

  return (
    <aside className="hidden md:flex w-[260px] flex-col bg-linear-to-b from-bg-dark to-bg-dark-2 border-r border-white/5 text-slate-300 shrink-0">
      {/* Header */}
      <div className="p-4 pb-2">
        <div className="flex items-center gap-2 mb-0.5">
          <BarChart3 size={18} className="text-primary-light" />
          <h1 className="text-white text-sm font-bold tracking-tight">Marketing Intelligence</h1>
        </div>
        <p className="text-[10px] font-mono text-slate-500">Multi-agent analytics · LangGraph</p>
      </div>

      <hr className="border-white/5 mx-4" />

      {/* New conversation */}
      <div className="p-4 pt-3 pb-2">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md bg-primary text-white text-xs font-semibold hover:bg-primary-light transition-colors cursor-pointer"
        >
          <MessageSquarePlus size={14} />
          New conversation
        </button>
      </div>

      {/* Example queries */}
      <div className="px-4 pt-1">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">Queries</h3>
        <div className="flex flex-col gap-1">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => onExampleClick(ex)}
              className="text-left text-xs px-2.5 py-1.5 rounded-md bg-white/[0.04] border border-white/[0.08] hover:bg-primary-light/10 hover:border-primary-light/30 hover:text-white transition-all cursor-pointer"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      <hr className="border-white/5 mx-4 mt-3" />

      {/* CSV Upload */}
      <div className="px-4 pt-2">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">Data</h3>
        <input ref={fileRef} type="file" accept=".csv" onChange={handleUpload} className="hidden" data-testid="csv-upload-input" />
        <button
          onClick={() => fileRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-md bg-white/[0.04] border border-white/[0.08] text-xs hover:bg-primary-light/10 hover:border-primary-light/30 hover:text-white transition-all cursor-pointer"
          data-testid="csv-upload-button"
        >
          <Upload size={12} />
          Upload CSV
        </button>
        {uploadStatus && (
          <p className="mt-1 text-[10px] font-mono text-slate-500 flex items-center gap-1" data-testid="upload-status">
            {uploadStatus.startsWith('Error') ? null : <CheckCircle size={10} className="text-success" />}
            {uploadStatus}
          </p>
        )}
      </div>

      <hr className="border-white/5 mx-4 mt-3" />

      {/* Agents */}
      <div className="px-4 pt-2">
        <h3 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">Agents</h3>
        <div className="text-xs space-y-1.5 text-slate-400">
          <p><strong className="text-slate-200">Supervisor</strong> — classify & route</p>
          <p><strong className="text-slate-200">Analytics</strong> — data, metrics, charts</p>
          <p><strong className="text-slate-200">Research</strong> — web, trends</p>
          <p><strong className="text-slate-200">Report</strong> — synthesis</p>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto p-4">
        <p className="font-mono text-[10px] text-slate-600">thread {threadId.slice(0, 8)}</p>
      </div>
    </aside>
  )
}
