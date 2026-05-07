import { useState, useCallback } from 'react'
import { uploadFile, listFiles, switchFile } from '../api'
import { useNavigate } from 'react-router-dom'

export default function Upload({ onFileActivated }) {
  const [dragging, setDragging]   = useState(false)
  const [uploading, setUploading] = useState(false)
  const [files, setFiles]         = useState([])
  const [profile, setProfile]     = useState(null)
  const [error, setError]         = useState(null)
  const navigate = useNavigate()

  const handleUpload = async (file) => {
    if (!file?.name.endsWith('.csv')) return setError('Only CSV files accepted')
    setUploading(true); setError(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await uploadFile(fd)
      setProfile(res.data.profile)
      onFileActivated(res.data.active_file)
      const fl = await listFiles()
      setFiles(fl.data.files)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed')
      console.error(e)
    } finally { setUploading(false) }
  }

  const handleSwitch = async (filename) => {
    await switchFile(filename)
    onFileActivated(filename)
    const fl = await listFiles()
    setFiles(fl.data.files)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragging(false)
    handleUpload(e.dataTransfer.files[0])
  }, [])

  return (
    <div style={{ padding: 40, maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, marginBottom: 8 }}>
        Upload Dataset
      </h1>
      <p style={{ color: 'var(--muted)', fontSize: 11, marginBottom: 32 }}>
        Upload a CSV — AnalystOS will profile it, index it, and make it queryable.
      </p>

      {/* drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => document.getElementById('file-input').click()}
        style={{
          border: `2px dashed ${dragging ? 'var(--blue)' : 'var(--border)'}`,
          borderRadius: 12, padding: '48px 24px', textAlign: 'center',
          cursor: 'pointer', transition: 'all 0.2s ease',
          background: dragging ? 'rgba(59,130,246,0.04)' : 'transparent',
          marginBottom: 32
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 12 }}>📂</div>
        <div style={{ fontSize: 13, color: 'var(--subtle)', marginBottom: 6 }}>
          {uploading ? 'Profiling dataset...' : 'Drop a CSV here or click to browse'}
        </div>
        <div style={{ fontSize: 10, color: 'var(--muted)' }}>Supported: .csv</div>
        <input id="file-input" type="file" accept=".csv" style={{ display: 'none' }}
          onChange={e => handleUpload(e.target.files[0])} />
      </div>

      {error && <div style={{ color: 'var(--red)', fontSize: 11, marginBottom: 16 }}>{error}</div>}

      {/* uploaded files */}
      {files.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 12, letterSpacing: 1 }}>
            UPLOADED FILES
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {files.map(f => (
              <div key={f.filename}
                onClick={() => handleSwitch(f.filename)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px 16px', borderRadius: 8, cursor: 'pointer',
                  border: `1px solid ${f.is_active ? 'var(--blue)' : 'var(--border)'}`,
                  background: f.is_active ? 'rgba(59,130,246,0.06)' : 'var(--surface)',
                  transition: 'all 0.15s ease'
                }}
              >
                <div>
                  <div style={{ fontSize: 12, marginBottom: 2 }}>{f.filename}</div>
                  <div style={{ fontSize: 9, color: 'var(--muted)' }}>
                    {f.rows.toLocaleString()} rows · {f.columns} columns
                  </div>
                </div>
                {f.is_active && (
                  <span style={{ fontSize: 9, color: 'var(--green)', 
                    border: '1px solid rgba(34,197,94,0.3)', 
                    padding: '2px 8px', borderRadius: 4 }}>ACTIVE</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* profile summary */}
      {profile && (
        <>
          <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 12, letterSpacing: 1 }}>
            PROFILE SUMMARY
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
            {[
              { label: 'Rows',     value: profile.shape.rows.toLocaleString(), color: 'var(--blue)' },
              { label: 'Columns',  value: profile.shape.columns,               color: 'var(--green)' },
              { label: 'Missing',  value: Object.keys(profile.missing||{}).length + ' cols', color: 'var(--amber)' },
              { label: 'Skewed',   value: Object.keys(profile.skewness||{}).length + ' cols', color: 'var(--amber)' },
              { label: 'Outliers', value: Object.keys(profile.outliers||{}).length + ' cols', color: 'var(--red)' },
              { label: 'Dupes',    value: profile.duplicates,                  color: 'var(--muted)' },
            ].map(s => (
              <div key={s.label} style={{
                padding: '14px 16px', borderRadius: 8,
                border: '1px solid var(--border)', background: 'var(--surface)'
              }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: s.color, marginBottom: 4 }}>
                  {s.value}
                </div>
                <div style={{ fontSize: 9, color: 'var(--muted)', letterSpacing: 0.5 }}>{s.label}</div>
              </div>
            ))}
          </div>

          <button onClick={() => navigate('/chat')} style={{
            background: 'var(--blue)', color: 'white', padding: '10px 24px',
            borderRadius: 6, fontSize: 11, fontWeight: 600
          }}>
            Start Analyzing →
          </button>
        </>
      )}
    </div>
  )
}