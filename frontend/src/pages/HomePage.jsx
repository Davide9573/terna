import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const DEFAULTS = { max_capacity: 100, k_pv: 3, k_w: 2, nuke: true }

export default function HomePage() {
  const [params, setParams] = useState(DEFAULTS)
  const navigate = useNavigate()

  const set = (e) => {
    const { name, value, type, checked } = e.target
    setParams(p => ({ ...p, [name]: type === 'checkbox' ? checked : Number(value) }))
  }

  return (
    <div className="page">
      <header className="app-header">
        <h1>Simulatore del Bilancio Energetico Italiano</h1>
        <p className="subtitle">Analisi degli scenari alternativi per la produzione di energia elettrica in Italia — dati TERNA 2025</p>
      </header>

      <main className="content">
        {/* Description */}
        <div className="card">
          <h2>Obiettivo della simulazione</h2>
          <p>
            Questo strumento simula l'evoluzione del mix energetico italiano a partire dai dati reali di
            produzione, consumo e scambio con l'estero relativi all'anno <strong>2025</strong>, forniti
            da <strong>TERNA</strong> (Gestore della Rete di Trasmissione Nazionale).
          </p>
          <p>
            Lo scenario simulato prevede il potenziamento delle fonti rinnovabili (fotovoltaico ed
            eolico), un incremento della capacità di accumulo energetico e, opzionalmente,
            l'introduzione di produzione nucleare. La simulazione calcola l'impatto sul consumo di
            energia termoelettrica e sull'importazione, nonché i costi incrementali annui.
          </p>
          <p>
            I parametri fisici ed economici del modello (rendimenti degli accumuli, costi livellati
            dell'energia LCOE/LCOS, costo dell'importazione) possono essere consultati e modificati
            nella pagina dedicata alla configurazione.
          </p>
        </div>

        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/config')}>
            ⚙️&nbsp; Configura i parametri del modello
          </button>
        </div>

        {/* Simulation params */}
        <div className="card">
          <h2>Parametri della simulazione</h2>
          <div className="params-grid">
            <div className="param-field">
              <label htmlFor="max_capacity">Capacità di accumulo</label>
              <div className="input-unit-row">
                <input id="max_capacity" name="max_capacity" type="number" min="0" step="10"
                       value={params.max_capacity} onChange={set} />
                <span className="unit-badge">GWh</span>
              </div>
              <p className="param-hint">Capacità massima aggiuntiva di accumulo (batterie + pompaggio idroelettrico)</p>
            </div>

            <div className="param-field">
              <label htmlFor="k_pv">Fattore fotovoltaico k&#x2091;&#x200b;&#x1D64;</label>
              <div className="input-unit-row">
                <input id="k_pv" name="k_pv" type="number" min="1" step="0.5"
                       value={params.k_pv} onChange={set} />
                <span className="unit-badge">×</span>
              </div>
              <p className="param-hint">Moltiplicatore della potenza fotovoltaica installata rispetto al 2025</p>
            </div>

            <div className="param-field">
              <label htmlFor="k_w">Fattore eolico k&#x1D64;</label>
              <div className="input-unit-row">
                <input id="k_w" name="k_w" type="number" min="1" step="0.5"
                       value={params.k_w} onChange={set} />
                <span className="unit-badge">×</span>
              </div>
              <p className="param-hint">Moltiplicatore della potenza eolica installata rispetto al 2025</p>
            </div>

            <div className="param-field param-field--checkbox">
              <label htmlFor="nuke">
                <input id="nuke" name="nuke" type="checkbox" checked={params.nuke} onChange={set} />
                <span>Includi produzione nucleare</span>
              </label>
              <p className="param-hint">
                La produzione termoelettrica residua viene rimpiazzata da nucleare con carico base garantito
                (pari al {30}% del picco) e surplus immagazzinato negli accumuli
              </p>
            </div>
          </div>

          <button className="btn btn-primary btn-large"
                  onClick={() => navigate('/results', { state: { params } })}>
            ▶&nbsp; Avvia simulazione
          </button>
        </div>
      </main>
    </div>
  )
}
