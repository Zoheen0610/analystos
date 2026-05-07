import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Upload   from './pages/Upload'
import Chat     from './pages/Chat'
import Graph    from './pages/Graph'
import Preprocess from './pages/Preprocess'
import { useState } from 'react'

export default function App() {
  const [activeFile, setActiveFile] = useState(null)

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar activeFile={activeFile} />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/"           element={<Upload onFileActivated={setActiveFile} />} />
          <Route path="/chat"       element={<Chat />} />
          <Route path="/graph"      element={<Graph />} />
          <Route path="/preprocess" element={<Preprocess />} />
        </Routes>
      </main>
    </div>
  )
}

function Sidebar({ activeFile }) {
  const links = [
    { to: '/',           label: 'Upload',     icon: '⬆' },
    { to: '/chat',       label: 'Chat',       icon: '💬' },
    { to: '/graph',      label: 'Graph',      icon: '🕸' },
    { to: '/preprocess', label: 'Preprocess', icon: '🔧' },
  ]

  return (
    <nav style={{
      width: 200, 
      background: 'rgba(8,12,22,0.75)',
      backdropFilter: 'blur(18px)',
      boxShadow: '0 0 40px rgba(0,0,0,0.35)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      padding: '24px 0', flexShrink: 0
    }}>
      <div style={{ padding: '0 20px 32px' }}>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 800 }}>
          Analyst<span style={{ color: 'var(--blue)' }}>OS</span>
        </div>
        <div style={{ fontSize: 9, color: 'var(--muted)', marginTop: 4 }}>
          AI Data Intelligence
        </div>
      </div>

      {links.map(l => (
        <NavLink key={l.to} to={l.to} end={l.to === '/'}
          style={({ isActive }) => ({
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '10px 20px', fontSize: 11,
            color: isActive ? 'var(--text)' : 'var(--muted)',
            background: isActive ? 'rgba(59,130,246,0.08)' : 'transparent',
            borderLeft: isActive ? '2px solid var(--blue)' : '2px solid transparent',
            textDecoration: 'none', transition: 'all 0.15s ease'
          })}
        >
          <span>{l.icon}</span> {l.label}
        </NavLink>
      ))}

      {activeFile && (
        <div style={{
          margin: '24px 16px 0',
          padding: '10px 12px',
          background: 'rgba(34,197,94,0.06)',
          border: '1px solid rgba(34,197,94,0.2)',
          borderRadius: 6, fontSize: 9, color: 'var(--green)'
        }}>
          <div style={{ marginBottom: 3, color: 'var(--muted)' }}>ACTIVE FILE</div>
          {activeFile}
        </div>
      )}
    </nav>
  )
}