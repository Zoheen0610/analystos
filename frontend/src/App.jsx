import { Routes, Route, NavLink } from 'react-router-dom'
import Upload     from './pages/Upload'
import Chat       from './pages/Chat'
import Graph      from './pages/Graph'
import Preprocess from './pages/Preprocess'
import { useState, useEffect } from 'react'

export default function App() {
  const [activeFile, setActiveFile] = useState(null)
  const [menuOpen, setMenuOpen]     = useState(false)
  const [isMobile, setIsMobile]     = useState(window.innerWidth < 768)

  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  // close menu on route change
  const closeMenu = () => setMenuOpen(false)

  return (
    <div style={{ display: 'flex', height: '100dvh', overflow: 'hidden', position: 'relative' }}>

      {/* sidebar — desktop always visible, mobile slide-in */}
      {(!isMobile || menuOpen) && (
        <>
          {/* backdrop on mobile */}
          {isMobile && (
            <div onClick={closeMenu} style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
              zIndex: 40, backdropFilter: 'blur(2px)'
            }} />
          )}

          <nav style={{
            width: 200, flexShrink: 0,
            background: 'rgba(8,12,22,0.92)',
            backdropFilter: 'blur(18px)',
            borderRight: '1px solid var(--border)',
            display: 'flex', flexDirection: 'column',
            padding: '24px 0',
            // mobile: fixed overlay
            ...(isMobile ? {
              position: 'fixed', top: 0, left: 0, bottom: 0,
              zIndex: 50, boxShadow: '4px 0 40px rgba(0,0,0,0.5)'
            } : {})
          }}>
            <div style={{ padding: '0 20px 32px' }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 800 }}>
                Analyst<span style={{ color: 'var(--blue)' }}>OS</span>
              </div>
              <div style={{ fontSize: 9, color: 'var(--muted)', marginTop: 4 }}>
                AI Data Intelligence
              </div>
            </div>

            {[
              { to: '/',           label: 'Upload',     icon: '⬆' },
              { to: '/chat',       label: 'Chat',       icon: '💬' },
              { to: '/graph',      label: 'Graph',      icon: '🕸' },
              { to: '/preprocess', label: 'Preprocess', icon: '🔧' },
            ].map(l => (
              <NavLink key={l.to} to={l.to} end={l.to === '/'}
                onClick={closeMenu}
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
                margin: '24px 16px 0', padding: '10px 12px',
                background: 'rgba(34,197,94,0.06)',
                border: '1px solid rgba(34,197,94,0.2)',
                borderRadius: 6, fontSize: 9, color: 'var(--green)'
              }}>
                <div style={{ marginBottom: 3, color: 'var(--muted)' }}>ACTIVE FILE</div>
                {activeFile}
              </div>
            )}
          </nav>
        </>
      )}

      {/* main content */}
      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>

        {/* mobile top bar */}
        {isMobile && (
  <div style={{
    position: 'sticky', top: 0, zIndex: 100,  // was 30, bump to 100
    display: 'flex', alignItems: 'center', gap: 12,
    padding: '12px 16px',
    background: 'rgba(6,7,11,0.97)',  // more opaque
    backdropFilter: 'blur(12px)',
    borderBottom: '1px solid var(--border)',
    boxShadow: '0 2px 20px rgba(0,0,0,0.4)'  // add shadow so it lifts above content
  }}>
            <button onClick={() => setMenuOpen(o => !o)} style={{
              background: 'none', border: '1px solid var(--border)',
              borderRadius: 6, padding: '6px 8px', color: 'var(--text)',
              fontSize: 14, lineHeight: 1, cursor: 'pointer'
            }}>
              ☰
            </button>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 14 }}>
              Analyst<span style={{ color: 'var(--blue)' }}>OS</span>
            </span>
          </div>
        )}

        <Routes>
          <Route path="/"           element={<Upload onFileActivated={setActiveFile} />} />
          <Route path="/chat"       element={<Chat />} />
          <Route path="/graph"      element={<Graph />} />
          <Route path="/preprocess" element={<Preprocess />} />
        </Routes>
      </div>
    </div>
  )
}