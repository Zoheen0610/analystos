import { useState } from 'react'
import { preprocessFull } from '../api'

export default function Preprocess() {
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied]   = useState(false)
  const [tab, setTab]         = useState('suggestions')

  const run = async () => {
    setLoading(true)
    try {
      const res = await preprocessFull()
      setResult(res.data)
    } catch (e) { alert(e.response?.data?.detail || 'Error') }
    finally { setLoading(false) }
  }

  const copy = () => {
    navigator.clipboard.writeText(result.step_2_code)
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  const priorityColor = { high: 'var(--red)', medium: 'var(--amber)', low: 'var(--muted)' }

  return (
    <div style={{ padding: 40, maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, marginBottom: 8 }}>
        Preprocessing
      </h1>
      <p style={{ color: 'var(--muted)', fontSize: 11, marginBottom: 32 }}>
        Two-step agentic pipeline — LLM reasons about issues, then generates grounded pandas code.
      </p>

      <button onClick={run} disabled={loading} style={{
        background: loading ? 'var(--border)' : 'var(--green)',
        color: loading ? 'var(--muted)' : 'var(--bg)',
        padding: '10px 28px', borderRadius: 8,
        fontSize: 12, fontWeight: 700, marginBottom: 32
      }}>
        {loading ? 'Analyzing...' : '▶ Run Pipeline'}
      </button>

      {result && (
        <>
          {/* tabs */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
            {['suggestions', 'code', 'hallucination'].map(t => (
              <button key={t} onClick={() => setTab(t)} style={{
                padding: '6px 14px', borderRadius: 6, fontSize: 10,
                background: tab === t ? 'var(--blue)' : 'var(--surface)',
                color: tab === t ? 'white' : 'var(--muted)',
                border: `1px solid ${tab === t ? 'var(--blue)' : 'var(--border)'}`
              }}>
                {t}
              </button>
            ))}
          </div>

          {/* suggestions tab */}
          {tab === 'suggestions' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {result.step_1_suggestions.map((s, i) => (
                <div key={i} style={{
                  padding: '14px 16px', borderRadius: 8,
                  border: `1px solid var(--border)`,
                  borderLeft: `3px solid ${priorityColor[s.priority] || 'var(--border)'}`,
                  background: 'var(--surface)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 11, fontWeight: 600 }}>{s.issue}</span>
                    <span style={{ fontSize: 9, color: priorityColor[s.priority] }}>
                      {s.priority?.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--subtle)', marginBottom: 4 }}>
                    <span style={{ color: 'var(--muted)' }}>column: </span>{s.column}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--subtle)', marginBottom: 4 }}>
                    <span style={{ color: 'var(--muted)' }}>action: </span>{s.action}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>
                    {s.reason}
                  </div>
                  {s.warning && (
                    <div style={{ fontSize: 9, color: 'var(--red)', marginTop: 6 }}>
                      ⚠ {s.warning}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* code tab */}
          {tab === 'code' && (
            <div style={{ position: 'relative' }}>
              <button onClick={copy} style={{
                position: 'absolute', top: 10, right: 10,
                background: 'var(--border)', color: 'var(--muted)',
                padding: '4px 10px', borderRadius: 4, fontSize: 9
              }}>
                {copied ? '✓ copied' : 'copy'}
              </button>
              <pre style={{
                background: 'var(--surface)', border: '1px solid var(--border)',
                borderRadius: 8, padding: '20px 16px', fontSize: 10,
                color: 'var(--subtle)', lineHeight: 1.7,
                overflow: 'auto', maxHeight: 600
              }}>
                {result.step_2_code}
              </pre>
            </div>
          )}

          {/* hallucination tab */}
          {tab === 'hallucination' && (
            <div style={{
              padding: '20px', borderRadius: 8,
              border: `1px solid ${result.hallucination_check.passed ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
              background: result.hallucination_check.passed ? 'rgba(34,197,94,0.04)' : 'rgba(239,68,68,0.04)'
            }}>
              <div style={{
                fontSize: 16, marginBottom: 12,
                color: result.hallucination_check.passed ? 'var(--green)' : 'var(--red)'
              }}>
                {result.hallucination_check.passed ? '✓ No hallucinations detected' : '⚠ Hallucinations detected'}
              </div>
              {!result.hallucination_check.passed && (
                <>
                  <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 8 }}>
                    Invented column names:
                  </div>
                  {result.hallucination_check.invented_columns.map((c, i) => (
                    <div key={i} style={{
                      display: 'inline-block', padding: '2px 8px', margin: '0 4px 4px 0',
                      background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                      borderRadius: 4, fontSize: 10, color: 'var(--red)'
                    }}>
                      {c}
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}