import { describe, it, expect, vi, beforeEach } from 'vitest'

// We test that the api module constructs correct fetch calls
describe('API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('healthCheck calls GET /api/health', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok', version: '0.2.0' }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { healthCheck } = await import('../../lib/api')
    const result = await healthCheck()

    expect(mockFetch).toHaveBeenCalledWith('/api/health')
    expect(result.status).toBe('ok')
  })

  it('sendQuery calls POST /api/query with body', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          thread_id: 't1',
          plan: ['analytics'],
          final_answer: 'answer',
          charts: [],
          sources: [],
          awaiting_approval: false,
        }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { sendQuery } = await import('../../lib/api')
    const result = await sendQuery('ROI', 'thread-1')

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/query',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ query: 'ROI', thread_id: 'thread-1' }),
      }),
    )
    expect(result.plan).toEqual(['analytics'])
  })

  it('approvePlan calls POST /api/approve', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          thread_id: 't1',
          plan: ['analytics'],
          final_answer: 'done',
          charts: [],
          sources: [],
          awaiting_approval: false,
        }),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { approvePlan } = await import('../../lib/api')
    await approvePlan('t1', ['analytics'])

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/approve',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ thread_id: 't1', plan: ['analytics'] }),
      }),
    )
  })
})
