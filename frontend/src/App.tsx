import { useState, useEffect } from 'react'
import ChatInterface from './components/ChatInterface'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import { SystemStatus } from './types'
import './App.css'

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Fetch system status on mount
    fetch('/api/status')
      .then(res => res.json())
      .then(data => {
        setStatus(data)
        setLoading(false)
      })
      .catch(err => {
        setError('Failed to connect to DS-Star system')
        setLoading(false)
        console.error('Status fetch error:', err)
      })
  }, [])

  if (loading) {
    return (
      <div className="app loading">
        <div className="loading-spinner"></div>
        <p>Initializing DS-Star System...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="app error">
        <div className="error-message">
          <h2>⚠️ Connection Error</h2>
          <p>{error}</p>
          <p className="error-hint">Make sure the backend server is running on port 8000</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <Header status={status} />
      <div className="app-content">
        <Sidebar specialists={status?.specialists || []} />
        <ChatInterface />
      </div>
    </div>
  )
}

export default App
