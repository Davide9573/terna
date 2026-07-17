import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import PowerChart from '../components/PowerChart'
import SummaryTable from '../components/SummaryTable'

export default function ResultsPage() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const params = state?.params

  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)

  useEffect(() => {
    if (!params) { navigate('/'); return }
    setLoading(true)
    fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setResults(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (!params) return null

  const paramSummary = `k_pv = ${params.k_pv}×  |  k_w = ${params.k_w}×  |  Accumulo = ${params.max_capacity} GWh  |  Nucleare: ${params.nuke ? 'Sì' : 'No'}`

  return (
    <div className="page">
      <header className="app-header">
        <h1>Risultati della simulazione</h1>
        <p className="subtitle">{paramSummary}</p>
      </header>

      <main className="content">
        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/')}>
            ← Torna alla pagina principale
          </button>
        </div>

        {loading && (
          <div className="loading-box">
            <div className="spinner" />
            <p>Simulazione in corso — attendere…</p>
          </div>
        )}

        {error && (
          <div className="error-box">
            <strong>Errore durante la simulazione:</strong> {error}
          </div>
        )}

        {results && (
          <>
            <section className="results-section">
              <h2>Scenario simulato</h2>
              <PowerChart
                chartData={results.after.chart}
                title="Bilancio energetico 2025 — Scenario simulato"
              />
              <SummaryTable
                energy={results.after.energy}
                peaks={results.after.chart.peaks}
              />
            </section>

            <section className="results-section">
              <h2>Costi annui dello scenario simulato aggiuntivi rispetto allo scenario attuale — 2025</h2>
              <CostTable costs={results.costs} />
            </section>
          </>
        )}
      </main>
    </div>
  )
}

function CostTable({ costs }) {
  const total = Object.values(costs).reduce((a, b) => a + b, 0)
  return (
    <div className="summary-table-wrapper">
      <table className="summary-table">
        <thead>
          <tr>
            <th>Fonte / Voce</th>
            <th>Costo aggiuntivo (miliardi $/anno)</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(costs).map(([src, cost]) => (
            <tr key={src}>
              <td>{src}</td>
              <td className={cost >= 0 ? 'cost-pos' : 'cost-neg'}>
                {cost >= 0 ? '+' : ''}{cost.toFixed(3)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td><strong>Totale</strong></td>
            <td className={total >= 0 ? 'cost-pos' : 'cost-neg'}>
              <strong>{total >= 0 ? '+' : ''}{total.toFixed(3)}</strong>
            </td>
          </tr>
        </tfoot>
      </table>
      <p style={{fontSize:'0.78rem', color:'#888', marginTop:'0.6rem'}}>
        Valori positivi = costo aggiuntivo rispetto allo scenario 2025; valori negativi = risparmio.
        Costi annualizzati sulla base della durata del dataset.
      </p>
    </div>
  )
}
