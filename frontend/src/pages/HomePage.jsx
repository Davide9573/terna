import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import PowerChart from '../components/PowerChart'
import SummaryTable from '../components/SummaryTable'

const DEFAULTS = { max_capacity: 100, k_pv: 3, k_w: 2, nuke: true }

export default function HomePage() {
  const navigate = useNavigate()
  const [currentScenario, setCurrentScenario] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    fetch('/api/current-scenario')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setCurrentScenario(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  return (
    <div className="page">
      <header className="app-header">
        <h1>Simulatore del Bilancio Energetico Italiano</h1>
        <p className="subtitle">Analisi degli scenari alternativi per la produzione di energia elettrica
          in Italia — dati TERNA 2025</p>
      </header>

      <main className="content">
        {/* Purpose and Context */}
        <div className="card">
          <h2>Scopo e contesto</h2>
          <p>
            Questo strumento è pensato per simulare l'effetto di differenti combinazioni del mix di fonti
            sul bilancio energetico italiano, a partire da dati reali, ovvero i valori di produzione, consumo e
            scambio con l'estero dell'anno <strong>2025</strong>.
            I dati sono quelli ufficiali, esatrtti dal sito web di <strong>TERNA</strong>, il gestore della rete
            di trasmissione nazionale (<a href="https://www.terna.it" target="_blank" rel="noopener noreferrer">www.terna.it</a>).<br />
          </p>
          <p>
            Nel recente passato, il dibattito pubblico ha spesso posto l'accento sulla necessità di incrementare
            la produzione di energia elettrica da fonti rinnovabili.
            Politici, ambientalisti ed eminenti scienziati hanno sostenuto che l'Italia potrebbe raggiungere
            l'autosufficienza energetica e la completa eliminazione delle fonti fossili (carbone, gas, olio
            combustibile), semplicemente aumentando la potenza installata di fotovoltaico ed eolico,
            e incrementando la capacità di accumulo.
          </p>
          <p>
            Questo strumento consente, in modo grossolano ma efficace, di verificare se tali affermazioni
            siano realistiche, e a quale costo.
          </p>
        </div>

        {/* Usage */}
        <div className="card">
          <h2>Come usare lo strumento</h2>
          <p>
            Premendo uno dei tre bottoni sottostanti l'applicativo consentirà di:<br />
            - modificare a proprio piacimento i parametri fisici ed economici che influenzano le simulazioni;<br />
            - simulare scenari che prevedono un differente mix di fonti energetiche;<br />
            - esplorare lo spazio degli scenari "a emissioni zero", confrontandone i costi.<br />
          </p>
          <p>
            Sotto ancora sono presentati i risultati dello scenario di riferimento, basato sui dati reali del 2025,
            in termini di:<br />
            - il grafico interattivo della distribuzione della potenza consumata, importata e generata, suddivisa per fonte;<br />
            - il prospetto tabulare dell'energia complessiva, dei relativi costi livellati (LCOE/LCOS)
            nel periodo di riferimento (il 2025), e dei picchi di potenza, sempre suddivisi per fonte.
          </p>
        </div>

        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/config')}>
            ⚙️&nbsp; Configura i parametri fisici<br /> ed economici del modello
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/simulation', { state: { params: DEFAULTS } })}>
            ▶️&nbsp; Esegui la simulazione di uno<br /> scenario alternativo
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/cost-analysis')}>
            💰&nbsp; Analizza i costi degli scenari<br /> a emissioni zero
          </button>
        </div>

        {/* Current Scenario — 2025 */}
        {loading && (
          <div className="loading-box">
            <div className="spinner" />
            <p>Caricamento dello scenario di riferimento (dati reali 2025)…</p>
          </div>
        )}

        {error && (
          <div className="error-box">
            <strong>Errore nel caricamento dei dati:</strong> {error}
          </div>
        )}

        {currentScenario && (
          <section className="results-section">
            <h2>Scenario di riferimento — dati reali 2025</h2>
            <PowerChart
              chartData={currentScenario.chart}
              title="Bilancio energetico 2025 — Scenario di riferimento"
            />
            <SummaryTable
              energy={currentScenario.energy}
              peaks={currentScenario.chart.peaks}
            />
          </section>
        )}
      </main>
    </div>
  )
}
