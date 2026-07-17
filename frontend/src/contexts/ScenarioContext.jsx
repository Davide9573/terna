import { createContext, useContext, useEffect, useState } from 'react'

const ScenarioContext = createContext(null)

export function ScenarioProvider({ children }) {
  const [currentScenario, setCurrentScenario] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Load data only once at app startup
    if (currentScenario !== null) return // Already loaded

    setLoading(true)
    fetch('/api/current-scenario')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setCurrentScenario(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, []) // Empty dependency array - runs only once

  return (
    <ScenarioContext.Provider value={{ currentScenario, loading, error }}>
      {children}
    </ScenarioContext.Provider>
  )
}

export function useCurrentScenario() {
  const ctx = useContext(ScenarioContext)
  if (!ctx) {
    throw new Error('useCurrentScenario must be used within ScenarioProvider')
  }
  return ctx
}
