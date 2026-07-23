import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DecarbonizationSurface from '../components/DecarbonizationSurface'

export default function CostAnalysisPage() {
  const navigate = useNavigate()
  const [surface, setSurface] = useState(null)
  const hasLoadedInitialCosts = useRef(false)
  const [ranges, setRanges] = useState({
    k_pv_range: 20,
    k_w_range: 20,
    storage_capacity_range_twh: 20,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const calculateCosts = () => {
    setLoading(true)
    setError(null)
    fetch('/api/decarbonization-surface', {
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
      .then(data => { setSurface(data.points); setLoading(false) })
      .catch(fetchError => { setError(fetchError.message); setLoading(false) })
  }

  useEffect(() => {
    if (hasLoadedInitialCosts.current) return
    hasLoadedInitialCosts.current = true
    calculateCosts()
  }, [])

  const handleRangeChange = (key, value) => {
    setRanges(currentRanges => ({ ...currentRanges, [key]: value }))
  }

  return (
    <div className="page">
      <header className="app-header">
        <h1>Analisi dei costi degli scenari a emissioni zero</h1>
        <p className="subtitle">Confronta i costi di diversi scenari alternativi</p>
      </header>

      <main className="content">
        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/')}>
            ← Indietro
          </button>
        </div>

        <section className="results-section">
          <h2>Obiettivo dell'analisi</h2>
          <p className="results-description-placeholder">
            Lo scopo di questa sezione è analizzare quali sono i possibili scenari in grado
            di decarbonizzare la produzione elettrica italiana senza ricorso al nucleare,
            e confrontarne i costi. <br />
            Il grafico seguente fornisce una rappresentazione della superficie di decarbonizzazione
            nello spazio dei parametri k_pv, k_w e capacità di accumulo, ovvero la superficie
            che delimita gli scenari a emissioni zero, quelli in cui è possibile annullare
            il ricorso alle fonti fossili.
            Il colore della superficie indica il costo livellato complessivo dello scenario,
            espresso in miliardi di euro all'anno.
          </p>
        </section>

        <section className="results-section">
          <h2>Intervallo dei parametri</h2>
          <div className="params-grid">
            <div className="param-field">
              <label htmlFor="k-pv-range">Range fattore k_pv</label>
              <div className="input-unit-row">
                <input
                  id="k-pv-range"
                  type="number"
                  min="1"
                  step="0.1"
                  value={ranges.k_pv_range}
                  onChange={event => handleRangeChange('k_pv_range', event.target.value)}
                />
                <span className="unit-badge">x</span>
              </div>
            </div>
            <div className="param-field">
              <label htmlFor="k-w-range">Range fattore k_w</label>
              <div className="input-unit-row">
                <input
                  id="k-w-range"
                  type="number"
                  min="1"
                  step="0.1"
                  value={ranges.k_w_range}
                  onChange={event => handleRangeChange('k_w_range', event.target.value)}
                />
                <span className="unit-badge">x</span>
              </div>
            </div>
            <div className="param-field">
              <label htmlFor="storage-capacity-range">Range capacita di accumulo</label>
              <div className="input-unit-row">
                <input
                  id="storage-capacity-range"
                  type="number"
                  min="0.001"
                  step="0.1"
                  value={ranges.storage_capacity_range_twh}
                  onChange={event => handleRangeChange('storage_capacity_range_twh', event.target.value)}
                />
                <span className="unit-badge">TWh</span>
              </div>
            </div>
          </div>
          <p>
            Attenzione: il ricalcolo può impiegare diversi secondi, a seconda dell'intervallo dei parametri selezionato.
          </p>
          <button className="btn btn-primary" onClick={calculateCosts} disabled={loading}>
            {loading ? 'Calcolo in corso...' : 'Ricalcola superficie e costi'}
          </button>
        </section>

        <section className="results-section">
          <h2>Superficie di decarbonizzazione</h2>
          {loading && (
            <div className="loading-box surface-loading">
              <div className="spinner" />
              <p>Calcolo della superficie di decarbonizzazione e dei costi in corso...</p>
            </div>
          )}
          {error && (
            <div className="error-box">
              <strong>Errore durante il calcolo della superficie:</strong> {error}
            </div>
          )}
          {surface && surface.length > 0 && <DecarbonizationSurface points={surface} />}
          {surface && surface.length === 0 && (
            <p className="results-description-placeholder">
              Non sono stati trovati scenari di decarbonizzazione nell'intervallo analizzato.
            </p>
          )}
        </section>
      </main>
    </div>
  )
}
