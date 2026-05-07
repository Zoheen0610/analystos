import { Routes, Route, NavLink } from 'react-router-dom'
import Upload     from './pages/Upload'
import Chat       from './pages/Chat'
import Graph      from './pages/Graph'
import Preprocess from './pages/Preprocess'
import { useState } from 'react'

export default function App() {
  const [activeFile, setActiveFile] = useState(null)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh', overflow: 'hidden' }}>
      <main style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/"           element={<Upload onFileActivated={setActiveFile} />} />
          <Route path="/chat"       element={<Chat />} />
          <Route path="/graph"      element={<Graph />} />
          <Route path="/preprocess" element={<Preprocess />} />
        </Routes>
      </main>
      <BottomNav activeFile={activeFile} />
    </div>
  )
}

function BottomNav({ activeFile }) {
  const links = [
    { to: '/',           label: 'Upload',  icon: '⬆' },
    { to: '/chat',       label: 'Chat',    icon: '💬' },
    { to: '/graph',      label: 'Graph',   icon: '🕸' },
    { to: '/preprocess', label: 'Prep',    icon: '🔧' },
  ]

  return (
    <nav style={{
      display: 'flex',
      borderTop: '1px solid var(--border)',
      background: 'rgba(8,12,22,0.92)',
      backdropFilter: 'blur(20px)',
      flexShrink: 0,
      paddingBottom: 'env(safe-area-inset-bottom)',
    }}>
      {links.map(l => (
        <NavLink key={l.to} to={l.to} end={l.to === '/'}
          style={({ isActive }) => ({
            flex: 1, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            padding: '10px 0', gap: 3, textDecoration: 'none',
            color: isActive ? 'var(--blue)' : 'var(--muted)',
            borderTop: isActive ? '2px solid var(--blue)' : '2px solid transparent',
            fontSize: 9, letterSpacing: 0.5,
            transition: 'all 0.15s ease'
          })}
        >
          <span style={{ fontSize: 18 }}>{l.icon}</span>
          {l.label}
        </NavLink>
      ))}
    </nav>
  )
}