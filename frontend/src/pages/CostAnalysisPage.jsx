import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DecarbonizationSurface from '../components/DecarbonizationSurface'
import PowerChart from '../components/PowerChart'
import SummaryTable from '../components/SummaryTable'

export default function CostAnalysisPage() {
  const navigate = useNavigate()
  const [surface, setSurface] = useState(null)
  const hasLoadedInitialCosts = useRef(false)
  const [nuclearScenario, setNuclearScenario] = useState(null)
  const hasLoadedNuclearScenario = useRef(false)
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

  useEffect(() => {
    if (hasLoadedNuclearScenario.current) return
    hasLoadedNuclearScenario.current = true
    fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        max_capacity: 0,
        k_pv: 1,
        k_w: 1,
        nuke: true,
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then(data => setNuclearScenario(data.after))
      .catch(fetchError => setError(fetchError.message))
  }, [])

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
          <p>
            Lo scopo di questa sezione è analizzare quali sono i possibili scenari in grado
            di decarbonizzare la produzione elettrica italiana senza ricorso al nucleare,
            e confrontarne i costi con la soluzione che intendesse perseguire la decarbonizzazione
            sostituendo il ricorso alle fonti fossili con il solo nucleare (mantenendo cioè
            invariata la potenza nominale delle fonti rinnovabili attuali). <br />
            I possibili scenari "a emissioni zero" privi di nucleare sono tanti, come tanti sono
            i possibili mix di fonti rinnovabili e di capacità di accumulo che si possono perseguire. <br />
            Il calcolo qui effettuato esegue una serie di simulazioni di scenario (analoghe a quelle che si
            possono eseguire nella sezione precedente) esplorando, in un intervallo definito dall'utente,
            le combinazioni dei tre parametri principali: <br />
            - il moltiplicatore della potenza nominale del fotovoltaico (k_pv), <br />
            - il moltiplicatore della potenza nominale dell'eolico (k_w) e <br />
            - la capacità di accumulo (in TWh) <br />
            Il risultato di queste simulazioni è una superficie nello spazio dei parametri, che delimita
            gli scenari a emissioni zero, ovvero quelli in cui è possibile annullare il ricorso alle fonti fossili
            senza ricorrere al nucleare.
            Il colore della superficie indica il costo livellato complessivo dello scenario, in miliardi di euro l'anno
            (si veda la legenda accanto), da confrontare con il costo dello scenario "a emissioni zero" ottenuto mediante
            nucleare, la cui simulazione è riportata in fondo alla pagina. <br />
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
            Modificare l'intervallo dei parametri da esplorare, e ricalcolare la superficie e i costi. <br />
            Attenzione: il ricalcolo può impiegare alcuni minuti, a seconda dell'intervallo dei parametri selezionato.
          </p>
          <button className="btn btn-primary" onClick={calculateCosts} disabled={loading}>
            {loading ? 'Calcolo in corso...' : 'Ricalcola superficie e costi'}
          </button>
        </section>

        <section className="results-section">
          <h2>Superficie di decarbonizzazione</h2>
          <p>
            Il grafico seguente fornisce una rappresentazione della superficie di decarbonizzazione
            nello spazio dei parametri k_pv, k_w e capacità di accumulo, ovvero la superficie
            che delimita gli scenari a emissioni zero, in cui è possibile annullare il ricorso alle fonti fossili
            senza ricorrere al nucleare.
            Il colore della superficie indica il costo livellato complessivo dello scenario, da confrontare con
            la legenda accanto, in miliardi di euro all'anno.
          </p>
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

        <section className="results-section">
          <h2>Scenario di decarbonizzazione mediante ricorso al nucleare</h2>
          {!nuclearScenario && !error && (
            <div className="loading-box">
              <div className="spinner" />
              <p>Simulazione dello scenario nucleare in corso...</p>
            </div>
          )}
          {nuclearScenario && (
            <>
              <PowerChart
                chartData={nuclearScenario.chart}
                title="Bilancio energetico 2025 - Scenario con nucleare"
              />
              <SummaryTable
                energy={nuclearScenario.energy}
                peaks={nuclearScenario.chart.peaks}
              />
            </>
          )}
        </section>
      </main>
    </div>
  )
}
