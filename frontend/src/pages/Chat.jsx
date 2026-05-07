import { useState, useRef, useEffect } from 'react'
import { sendChat, evalQuery, searchColumns, listFiles, switchFile } from '../api'

const isMobile = () => window.innerWidth < 768

export default function Chat() {
  const [messages, setMessages]     = useState([])
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [evalMode, setEvalMode]     = useState(false)
  const [search, setSearch]         = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [files, setFiles]           = useState([])
  const [showSearch, setShowSearch] = useState(false)
  const [mobile, setMobile]         = useState(isMobile())
  const bottomRef = useRef(null)

  useEffect(() => {
    listFiles().then(r => setFiles(r.data.files)).catch(() => {})
    const handler = () => setMobile(isMobile())
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
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
      setMessages(m => [...m, {
        role: 'assistant',
        content: '⚠ ' + (e.response?.data?.detail || 'Error'),
        isError: true
      }])
    } finally { setLoading(false) }
  }

  const handleSearch = async () => {
    if (!search.trim()) return
    const res = await searchColumns(search)
    setSearchResults(res.data.results)
  }

  return (
    <div style={{
      display: 'flex',
      height: mobile ? 'calc(100dvh - 49px)' : '100dvh',
      overflow: 'hidden'
    }}>

      {/* main chat */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>

        {/* header */}
        <div style={{
          padding: mobile ? '12px 16px' : '20px 28px',
          borderBottom: '1px solid var(--border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexShrink: 0
        }}>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: mobile ? 13 : 16 }}>
              Chat
            </div>
            <div style={{ fontSize: 9, color: 'var(--muted)', marginTop: 2 }}>
              RAG-grounded · graph-aware
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: mobile ? 8 : 12 }}>
            {/* mobile search toggle */}
            {mobile && (
              <button onClick={() => setShowSearch(s => !s)} style={{
                background: showSearch ? 'var(--blue-soft)' : 'none',
                border: '1px solid var(--border)',
                borderRadius: 6, padding: '5px 8px',
                color: 'var(--muted)', fontSize: 12
              }}>🔍</button>
            )}

            <div style={{ fontSize: 10, color: 'var(--muted)' }}>
              {mobile ? 'Eval' : 'Eval mode'}
            </div>
            <div onClick={() => setEvalMode(e => !e)} style={{
              width: 36, height: 20, borderRadius: 10, cursor: 'pointer',
              background: evalMode ? 'var(--blue)' : 'var(--border)',
              position: 'relative', transition: 'background 0.2s ease', flexShrink: 0
            }}>
              <div style={{
                position: 'absolute', top: 3, width: 14, height: 14,
                borderRadius: '50%', background: 'white', transition: 'left 0.2s ease',
                left: evalMode ? 19 : 3
              }} />
            </div>
          </div>
        </div>

        {/* mobile search drawer */}
        {mobile && showSearch && (
          <div style={{
            padding: '12px 16px', borderBottom: '1px solid var(--border)',
            background: 'var(--surface)', flexShrink: 0
          }}>
            <div style={{ fontSize: 9, color: 'var(--muted)', letterSpacing: 1, marginBottom: 8 }}>
              SEMANTIC COLUMN SEARCH
            </div>
            <div style={{ display: 'flex', gap: 6, marginBottom: searchResults.length ? 10 : 0 }}>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                placeholder="e.g. price related..."
                style={{
                  flex: 1, borderRadius: 6,
                  padding: '7px 10px', fontSize: 10
                }}
              />
              <button onClick={handleSearch} style={{
                background: 'var(--blue)', color: 'white',
                padding: '7px 10px', borderRadius: 6, fontSize: 10
              }}>→</button>
            </div>
            {searchResults.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {searchResults.map((r, i) => (
                  <div key={i} style={{
                    padding: '4px 8px', borderRadius: 4,
                    border: '1px solid var(--border)',
                    background: 'var(--bg)', fontSize: 9
                  }}>
                    {r.column || r.message}
                    {r.similarity && <span style={{ color: 'var(--blue)', marginLeft: 4 }}>{r.similarity}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* messages */}
        <div style={{
          flex: 1, overflow: 'auto',
          padding: mobile ? '16px' : '24px 28px',
          display: 'flex', flexDirection: 'column', gap: 16
        }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: 60, color: 'var(--muted)', fontSize: 12 }}>
              <div style={{ fontSize: 28, marginBottom: 12 }}>💬</div>
              Ask anything about your dataset
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{ maxWidth: mobile ? '90%' : '75%' }}>
                <div style={{
                  padding: '10px 14px', borderRadius: 10,
                  fontSize: mobile ? 13 : 12, lineHeight: 1.7,
                  background: m.role === 'user' ? 'var(--blue)' : 'var(--surface)',
                  border: m.role === 'user' ? 'none' : '1px solid var(--border)',
                  color: m.isError ? 'var(--red)' : 'var(--text)',
                  wordBreak: 'break-word'
                }}>
                  {m.content}
                </div>

                {m.meta && (
                  <div style={{
                    marginTop: 6, padding: '6px 10px', fontSize: 9, color: 'var(--muted)',
                    background: 'rgba(30,58,95,0.3)', borderRadius: 6,
                    border: '1px solid var(--border)', lineHeight: 1.8
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
                        <> · <span style={{ color: 'var(--amber)' }}>
                          +{m.meta.graph_nodes_used.length} graph nodes
                        </span></>
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
                border: '1px solid var(--border)', borderRadius: 10,
                fontSize: 12, color: 'var(--muted)'
              }}>
                thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* input */}
        <div style={{
          padding: mobile ? '12px 16px' : '16px 28px',
          borderTop: '1px solid var(--border)',
          display: 'flex', gap: 8, flexShrink: 0,
          paddingBottom: mobile ? 'max(12px, env(safe-area-inset-bottom))' : '16px'
        }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about your dataset..."
            style={{
              flex: 1, borderRadius: 8,
              padding: mobile ? '12px 14px' : '10px 14px',
              fontSize: mobile ? 14 : 12
            }}
          />
          <button onClick={send} disabled={loading} style={{
            background: loading ? 'var(--border)' : 'var(--blue)',
            color: 'white', padding: '10px 16px', borderRadius: 8,
            fontSize: 11, flexShrink: 0
          }}>
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>

      {/* right panel — desktop only */}
      {!mobile && (
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
                  flex: 1, borderRadius: 6,
                  padding: '7px 10px', fontSize: 10
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
      )}
    </div>
  )
}