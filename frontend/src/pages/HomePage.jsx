import { useNavigate } from 'react-router-dom'
import PowerChart from '../components/PowerChart'
import SummaryTable from '../components/SummaryTable'
import { useCurrentScenario } from '../contexts/ScenarioContext'

const DEFAULTS = { max_capacity: 100, k_pv: 3, k_w: 2, nuke: true }

export default function HomePage() {
  const navigate = useNavigate()
  const { currentScenario, loading, error } = useCurrentScenario()

  return (
    <div className="page">
      <header className="app-header">
        <h1>Decarbonizzare la produzione elettrica italiana è possibile?
          Anche senza ricorso al nucleare? E a quale costo?</h1>
        <p className="subtitle">Analisi degli scenari alternativi a quello attuale — dati TERNA 2025</p>
      </header>

      <main className="content">
        {/* Purpose and Context */}
        <div className="card">
          <h2>Scopo e contesto</h2>
          <p>
            Questo strumento è pensato per simulare l'effetto di differenti combinazioni del mix di fonti
            sul bilancio energetico italiano, a partire da dati reali, ovvero i valori di produzione, consumo e
            scambio con l'estero dell'anno <strong>2025</strong>.
            I dati sono quelli ufficiali, estratti dal sito web di <strong>TERNA</strong>, il gestore della rete
            di trasmissione nazionale (<a href="https://www.terna.it" target="_blank" rel="noopener noreferrer">www.terna.it</a>).<br />
          </p>
          <p>
            Il dibattito pubblico pone spesso l'accento sulla necessità di incrementare
            la produzione di energia elettrica da fonti rinnovabili.
            Politici, ambientalisti ed eminenti scienziati sostengono che l'Italia potrebbe raggiungere
            l'autosufficienza energetica e la completa eliminazione delle fonti fossili (carbone, gas, olio
            combustibile), semplicemente aumentando la potenza installata di fotovoltaico ed eolico,
            e incrementando al contempo la capacità di accumulo.
          </p>
          <p>
            Questo strumento consente, in modo grossolano ma efficace, di verificare se tali affermazioni
            siano realistiche.
          </p>
        </div>

        {/* Usage */}
        <div className="card">
          <h2>Come usare lo strumento</h2>
          <p>
            Premendo uno dei tre bottoni sottostanti l'applicativo consentirà di:<br />
            - modificare a proprio piacimento i parametri fisici ed economici che influenzano tutte le simulazioni;<br />
            - simulare scenari che prevedono un differente mix di fonti energetiche;<br />
            - esplorare lo spazio degli scenari "a emissioni zero", con e senza ricorso al nucleare, confrontandone i costi.<br />
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
            <p>Caricamento dello scenario di riferimento (dati ufficiali 2025)…</p>
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
            <p>
              Di seguito il grafico della distribuzione della potenza consumata, importata e generata, suddivisa per fonte.<br />
              Il grafico è interattivo: è possibile fare pan e zoom per esplorare i dettagli della distribuzione.<br />
            </p>
            <PowerChart
              chartData={currentScenario.chart}
              title="Bilancio energetico 2025 — Scenario di riferimento"
            />
            <p>
              Qui sotto il prospetto tabulare, sempre suddiviso per fonte, dell'energia complessiva nel periodo di riferimento,
              dei relativi costi livellati (LCOE/LCOS), e dei picchi di potenza.
            </p>
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
