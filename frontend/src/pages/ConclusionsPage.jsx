import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

const DEFAULT_RANGES = {
  k_pv_range: 20,
  k_w_range: 20,
  storage_capacity_range_twh: 20,
}

export default function ConclusionsPage() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const [costs, setCosts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const ranges = state?.ranges ?? DEFAULT_RANGES
    fetch('/api/conclusions-cost-comparison', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        k_pv_range: Number(ranges.k_pv_range),
        k_w_range: Number(ranges.k_w_range),
        storage_capacity_range_twh: Number(ranges.storage_capacity_range_twh),
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then(data => { setCosts(data); setLoading(false) })
      .catch(fetchError => { setError(fetchError.message); setLoading(false) })
  }, [state])

  return (
    <div className="page">
      <header className="app-header">
        <h1>Conclusioni</h1>
      </header>

      <main className="content">
        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/cost-analysis')}>
            ← Torna all'analisi dei costi
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/')}>
            ← Torna alla pagina principale
          </button>
        </div>

        <section className="results-section conclusions-section">
          <div className="conclusions-text">
            <h2>Conclusioni</h2>
            <p>
              Le simulazioni eseguite presentano una serie di approssimazioni grossolane,
              ma consentono di trarre alcune conclusioni di carattere generale, che possono essere utili
              per orientare le scelte di politica energetica in ottica di decarbonizzazione, cioè
              di rinuncia totale ai combustibili fossili.
            </p>
          </div>
        </section>

        <section className="results-section">
          <h2>Confronto dei costi livellati</h2>
          {loading && (
            <div className="loading-box">
              <div className="spinner" />
              <p>Calcolo del confronto dei costi in corso...</p>
            </div>
          )}
          {error && (
            <div className="error-box">
              <strong>Errore durante il calcolo del confronto:</strong> {error}
            </div>
          )}
          {costs && <LevelizedCostTable costs={costs} />}
        </section>
      </main>
    </div>
  )
}

function LevelizedCostTable({ costs }) {
  const sources = Object.keys(costs.reference)

  return (
    <div className="summary-table-wrapper">
      <table className="summary-table">
        <thead>
          <tr>
            <th>Fonte / Voce</th>
            <th>Scenario di riferimento (2025)</th>
            <th>Scenario più economico senza nucleare</th>
            <th>Scenario più economico con nucleare</th>
          </tr>
        </thead>
        <tbody>
          {sources.map(source => (
            <tr key={source} className={source === 'Total' ? 'total-row' : ''}>
              <td>{source === 'Total' ? <strong>Totale</strong> : source}</td>
              <td>{costs.reference[source].toFixed(3)}</td>
              <td>{costs.without_nuclear[source].toFixed(3)}</td>
              <td>{costs.with_nuclear[source].toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="table-note">Costi livellati annui in G€/anno.</p>
    </div>
  )
}