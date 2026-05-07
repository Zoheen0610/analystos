import { useState, useEffect, useRef } from 'react'
import { getGraph, summarizeSession, listSummaries, compareSessions, evalSession } from '../api'

export default function Graph() {
  const [graphData, setGraphData]     = useState(null)
  const [summaries, setSummaries]     = useState([])
  const [comparing, setComparing]     = useState([])
  const [comparison, setComparison]   = useState(null)
  const [sessionEval, setSessionEval] = useState(null)
  const [loading, setLoading]         = useState(false)
  const iframeRef = useRef(null)

  const refresh = async () => {
    try {
      const [g, s] = await Promise.all([getGraph(), listSummaries().catch(() => ({ data: { summaries: [] } }))])
      setGraphData(g.data)
      setSummaries(s.data.summaries || [])
    } catch {}
  }

  useEffect(() => { refresh() }, [])

  const handleSummarize = async () => {
    setLoading(true)
    try { await summarizeSession(); await refresh() }
    catch (e) { alert(e.response?.data?.detail || 'Error') }
    finally { setLoading(false) }
  }

  const toggleCompare = (nodeId) => {
    setComparing(prev =>
      prev.includes(nodeId) ? prev.filter(x => x !== nodeId)
      : prev.length < 2 ? [...prev, nodeId] : [prev[1], nodeId]
    )
    setComparison(null)
  }

  const handleCompare = async () => {
    if (comparing.length < 2) return
    const res = await compareSessions(comparing[0], comparing[1])
    setComparison(res.data)
  }

  const handleEval = async () => {
    const res = await evalSession()
    setSessionEval(res.data)
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>

      {/* graph iframe */}
      <div style={{ flex: 1, position: 'relative' }}>
        <iframe
          ref={iframeRef}
          src="http://localhost:8000/graph/visualize"
          style={{ width: '100%', height: '100%', border: 'none' }}
          title="Workflow Graph"
        />
        <button onClick={refresh} style={{
          position: 'absolute', top: 16, right: 16,
          background: 'var(--surface)', border: '1px solid var(--border)',
          color: 'var(--muted)', padding: '6px 12px', borderRadius: 6, fontSize: 10
        }}>↻ Refresh</button>
      </div>

      {/* right panel */}
      <div style={{
        width: 300, borderLeft: '1px solid var(--border)',
        background: 'var(--surface)', display: 'flex',
        flexDirection: 'column', overflow: 'auto'
      }}>

        {/* summarize */}
        <div style={{ padding: '20px 16px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 1, marginBottom: 10 }}>
            SESSION
          </div>
          <button onClick={handleSummarize} disabled={loading} style={{
            width: '100%', background: 'var(--amber)', color: 'var(--bg)',
            padding: '8px 0', borderRadius: 6, fontSize: 11, fontWeight: 600
          }}>
            {loading ? 'Summarizing...' : '+ Summarize Session'}
          </button>
          <button onClick={handleEval} style={{
            width: '100%', marginTop: 8,
            background: 'transparent', border: '1px solid var(--border)',
            color: 'var(--muted)', padding: '8px 0', borderRadius: 6, fontSize: 11
          }}>
            View Session Health
          </button>
        </div>

        {/* session eval */}
        {sessionEval && (
          <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 1, marginBottom: 10 }}>
              SESSION HEALTH
            </div>
            {Object.entries(sessionEval.session_health).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 10 }}>
                <span style={{ color: 'var(--muted)' }}>{k.replace(/_/g, ' ')}</span>
                <span style={{ color: 'var(--blue)' }}>{v}</span>
              </div>
            ))}
          </div>
        )}

        {/* summaries + compare */}
        {summaries.length > 0 && (
          <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 1, marginBottom: 10 }}>
              SESSIONS — select 2 to compare
            </div>
            {summaries.map(s => (
              <div key={s.node_id}
                onClick={() => toggleCompare(s.node_id)}
                style={{
                  padding: '8px 10px', marginBottom: 6, borderRadius: 6, cursor: 'pointer',
                  border: `1px solid ${comparing.includes(s.node_id) ? 'var(--blue)' : 'var(--border)'}`,
                  background: comparing.includes(s.node_id) ? 'rgba(59,130,246,0.06)' : 'var(--bg)'
                }}
              >
                <div style={{ fontSize: 10, marginBottom: 3 }}>{s.node_id} · {s.date}</div>
                <div style={{ fontSize: 9, color: 'var(--muted)', lineHeight: 1.5 }}>
                  {s.summary.slice(0, 80)}...
                </div>
              </div>
            ))}

            {comparing.length === 2 && (
              <button onClick={handleCompare} style={{
                width: '100%', background: 'var(--blue)', color: 'white',
                padding: '8px 0', borderRadius: 6, fontSize: 11, marginTop: 8
              }}>
                Compare Sessions
              </button>
            )}
          </div>
        )}

        {/* comparison result */}
        {comparison && (
          <div style={{ padding: '16px' }}>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 1, marginBottom: 10 }}>
              COMPARISON RESULT
            </div>
            <div style={{
              padding: '10px 12px', borderRadius: 6, marginBottom: 12,
              background: 'rgba(59,130,246,0.06)', border: '1px solid var(--border)'
            }}>
              <div style={{ fontSize: 11, marginBottom: 4 }}>
                similarity: <span style={{ color: 'var(--blue)', fontWeight: 600 }}>
                  {comparison.overall_similarity}
                </span>
              </div>
              <div style={{ fontSize: 10, color: 'var(--muted)' }}>{comparison.similarity_label}</div>
            </div>

            {comparison.new_focus_in_session_b?.length > 0 && (
              <>
                <div style={{ fontSize: 9, color: 'var(--green)', letterSpacing: 1, marginBottom: 6 }}>
                  NEW IN SESSION B
                </div>
                {comparison.new_focus_in_session_b.map((s, i) => (
                  <div key={i} style={{
                    fontSize: 9, color: 'var(--subtle)', lineHeight: 1.6, marginBottom: 6,
                    padding: '6px 8px', borderLeft: '2px solid var(--green)',
                    background: 'rgba(34,197,94,0.04)'
                  }}>
                    {s}
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}