import { useState, useRef, useEffect } from 'react'
import { sendChat, evalQuery, searchColumns, listFiles, switchFile } from '../api'

export default function Chat() {
  const [messages, setMessages]   = useState([])
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [evalMode, setEvalMode]   = useState(false)
  const [search, setSearch]       = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [files, setFiles]         = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    listFiles().then(r => setFiles(r.data.files)).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const q = input.trim(); setInput(''); setLoading(true)
    setMessages(m => [...m, { role: 'user', content: q }])
    try {
      const fn = evalMode ? evalQuery : sendChat
      const res = await fn(q)
      const d = res.data
      setMessages(m => [...m, {
        role: 'assistant',
        content: d.answer,
        meta: evalMode ? d.eval : {
          retrieval_metadata: d.retrieval_metadata,
          graph_nodes_used: d.graph_nodes_used
        }
      }])
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: '⚠ ' + (e.response?.data?.detail || 'Error'), isError: true }])
    } finally { setLoading(false) }
  }

  const handleSearch = async () => {
    if (!search.trim()) return
    const res = await searchColumns(search)
    setSearchResults(res.data.results)
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>

      {/* main chat */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

        {/* header */}
        <div style={{
          padding: '20px 28px', borderBottom: '1px solid var(--border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 16 }}>Chat</div>
            <div style={{ fontSize: 9, color: 'var(--muted)', marginTop: 2 }}>
              RAG-grounded · graph-aware
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ fontSize: 10, color: 'var(--muted)' }}>Eval mode</div>
            <div onClick={() => setEvalMode(e => !e)} style={{
              width: 36, height: 20, borderRadius: 10, cursor: 'pointer',
              background: evalMode ? 'var(--blue)' : 'var(--border)',
              position: 'relative', transition: 'background 0.2s ease'
            }}>
              <div style={{
                position: 'absolute', top: 3, width: 14, height: 14,
                borderRadius: '50%', background: 'white', transition: 'left 0.2s ease',
                left: evalMode ? 19 : 3
              }} />
            </div>
          </div>
        </div>

        {/* messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: 80, color: 'var(--muted)', fontSize: 12 }}>
              <div style={{ fontSize: 28, marginBottom: 12 }}>💬</div>
              Ask anything about your dataset
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{ maxWidth: '75%' }}>
                <div style={{
                  padding: '10px 14px', borderRadius: 10, fontSize: 12, lineHeight: 1.7,
                  background: m.role === 'user' ? 'var(--blue)' : 'var(--surface)',
                  border: m.role === 'user' ? 'none' : '1px solid var(--border)',
                  color: m.isError ? 'var(--red)' : 'var(--text)'
                }}>
                  {m.content}
                </div>

                {/* metadata */}
                {m.meta && (
                  <div style={{
                    marginTop: 6, padding: '8px 12px', fontSize: 9, color: 'var(--muted)',
                    background: 'rgba(30,58,95,0.3)', borderRadius: 6,
                    border: '1px solid var(--border)'
                  }}>
                    {m.meta.retrieval && <>
                      <span style={{ color: 'var(--blue)' }}>relevance </span>
                      {m.meta.retrieval.avg_relevance_score} ·{' '}
                      <span style={{ color: 'var(--blue)' }}>coverage </span>
                      {m.meta.retrieval.coverage_percent}% ·{' '}
                      <span style={{ color: m.meta.hallucination?.hallucination_detected ? 'var(--red)' : 'var(--green)' }}>
                        {m.meta.hallucination?.hallucination_detected ? '⚠ hallucination' : '✓ clean'}
                      </span>
                    </>}
                    {m.meta.retrieval_metadata && <>
                      {m.meta.retrieval_metadata.map(r => r.section).join(' · ')}
                      {m.meta.graph_nodes_used?.length > 0 &&
                        <> · <span style={{ color: 'var(--amber)' }}>+{m.meta.graph_nodes_used.length} graph nodes</span></>
                      }
                    </>}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                padding: '10px 14px', background: 'var(--surface)',
                border: '1px solid var(--border)', borderRadius: 10, fontSize: 12, color: 'var(--muted)'
              }}>
                thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* input */}
        <div style={{ padding: '16px 28px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about your dataset..."
            style={{
              flex: 1, background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 8, padding: '10px 14px', fontSize: 12, color: 'var(--text)'
            }}
          />
          <button onClick={send} disabled={loading} style={{
            background: loading ? 'var(--border)' : 'var(--blue)',
            color: 'white', padding: '10px 20px', borderRadius: 8, fontSize: 11
          }}>
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>

      {/* right panel — semantic search */}
      <div style={{
        width: 260, borderLeft: '1px solid var(--border)',
        background: 'var(--surface)', display: 'flex', flexDirection: 'column'
      }}>
        <div style={{ padding: '20px 16px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 1, marginBottom: 12 }}>
            SEMANTIC COLUMN SEARCH
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. price related..."
              style={{
                flex: 1, background: 'var(--bg)', border: '1px solid var(--border)',
                borderRadius: 6, padding: '7px 10px', fontSize: 10, color: 'var(--text)'
              }}
            />
            <button onClick={handleSearch} style={{
              background: 'var(--blue)', color: 'white',
              padding: '7px 10px', borderRadius: 6, fontSize: 10
            }}>→</button>
          </div>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          {searchResults.map((r, i) => (
            <div key={i} style={{
              padding: '8px 10px', marginBottom: 6, borderRadius: 6,
              border: '1px solid var(--border)', background: 'var(--bg)'
            }}>
              <div style={{ fontSize: 11, marginBottom: 2 }}>{r.column || r.message}</div>
              {r.similarity && (
                <div style={{ fontSize: 9, color: 'var(--muted)' }}>
                  similarity: <span style={{ color: 'var(--blue)' }}>{r.similarity}</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* file switcher */}
        {files.length > 0 && (
          <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: 9, color: 'var(--muted)', marginBottom: 8, letterSpacing: 1 }}>
              SWITCH FILE
            </div>
            {files.map(f => (
              <div key={f.filename}
                onClick={() => switchFile(f.filename).then(() => listFiles().then(r => setFiles(r.data.files)))}
                style={{
                  padding: '6px 8px', borderRadius: 4, cursor: 'pointer', fontSize: 9,
                  color: f.is_active ? 'var(--green)' : 'var(--muted)',
                  background: f.is_active ? 'rgba(34,197,94,0.06)' : 'transparent',
                  marginBottom: 2
                }}
              >
                {f.is_active ? '● ' : '○ '}{f.filename}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}