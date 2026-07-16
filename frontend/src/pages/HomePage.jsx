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
        <p className="subtitle">Analisi degli scenari alternativi per la produzione di energia elettrica
          in Italia — dati TERNA 2025</p>
      </header>

      <main className="content">
        {/* Description */}
        <div className="card">
          <h2>Obiettivo e criteri adottati per la simulazione</h2>
          <p>
            Questo strumento è pensato per simulare l'effetto di differenti combinazioni del mix di fonti
            sul bilancio energetico italiano, a partire dai dati reali.
            I dati reali sono quelli di produzione, consumo e scambio con l'estero relativi all'anno <strong>2025</strong>,
            forniti da <strong>TERNA</strong>, il gestore della rete di trasmissione nazionale, consultabili dal
            sito web (<a href="https://www.terna.it" target="_blank" rel="noopener noreferrer">www.terna.it</a>).<br />
            Lo scopo della simulazione è quello di valutare l'impatto economico di un incremento della
            produzione da fonti rinnovabili, e verificare se sia possibile ridurre o eliminare la generazione
            di energia elettrica da fonti fossili (carbone, gas, olio combustibile) e l'importazione dall'estero.
          </p>
          <p>
            Lo strumento consente di alterare il mix corrente per simulare scenari che prevedono:<br />
            - il potenziamento delle fonti rinnovabili di tipo fotovoltaico ed eolico,<br />
            - l'incremento della capacità di accumulo energetico (elettrochimico o da pompaggio idrico),<br />
            - l'eventuale introduzione di produzione nucleare.<br />
            La simulazione calcola la nuova distribuzione tra le varie fonti, valutando in particolare l'impatto
            sul consumo di energia termoelettrica, sull'importazione, e sui costi annui.
            A tal fine vengono fatte alcune assunzioni, e commesse alcune approssimazioni, grossolane ma necessarie.
          </p>
          <p>
            Assunzioni:<br />
            - il fabbisogno puntuale di energia elettrica non viene alterato, ed <strong>è vincolato</strong> ad
            essere pari a quello del 2025;<br />
            - la potenza fotovoltaica e quella eolica sono ottenute come semplice riscalatura delle rispettive potenze
            correnti (in altre parole, si assume che la produzione da rinnovabili non controllabili sia proporzionale
            alla potenza installata, e la rispettiva modulazione temporale sia dettata dalla presenza di sole e vento);<br />
            - ove possibile, cioè in caso di produzione in eccesso, prioritariamente la potenza termoelettrica, e
            a seguire quella importata dall'estero, vengono ridotte fino ad annullarsi,
            in modo da azzerare il ricorso a fonti fossili e importazione;<br />
            - l'energia in surplus viene immagazzinata negli accumuli, fino a capienza massima degli stessi;<br />
            - laddove il surplus di potenza rinnovabile non sia sufficiente ad azzerare il ricorso a termoelettrico e
            importazione, e qualora ci sia capacità residua negli accumuli, questa viene utilizzata per coprire il
            fabbisogno;<br />
            - l'energia accumulata può essere caricata e scaricata in qualsiasi momento, senza vincoli di potenza,
            ma tenendo conto dei rispettivi rendimenti, di carica e scarica;<br />
            - qualora il mix delle fonti ammetta il ricorso al nucleare, questo viene considerato come possibile fonte
            per azzerare il ricorso a termoelettrico e importazione, con priorità inferiore solo alle rinnovabili;<br />
            - viene considerato un limite fisico alla modulabilità del nucleare: la potenza minima prodotta, in
            qualunque istante, non può mai essere inferiore ad una percentuale fissata del picco annuo di potenza,
            che dunque viene a costituire il carico base garantito;<br />
            - nella simulazione dell'impatto economico sono contemplati i costi livellati di tutte le fonti
            (rinnovabili, termico e nucleare), quelli dell'accumulo, ed il risparmio per minore importazione.
          </p>
          <p>
            Approssimazioni:<br />
            - non viene posto alcun limite alla potenza di carica e scarica degli accumuli, ma solo alla
            capacità massima;<br />
            - non vengono considerati i costi di realizzazione e gestione dei sistemi di conversione da corrente
            continua ad alternata;<br />
            - non viene considerata la distribuzione geografica della produzione e dei consumi, e dunque i costi
            aggiuntivi di trasporto, quelli dovuti alle perdite, né quelli di bilanciamento della rete per prevenire
            i rischi di congestione.
          </p>
          <p>
            I parametri fisici ed economici del modello (rendimenti di carica e scarica degli accumuli,
            costi livellati dell'energia LCOE/LCOS, costo dell'importazione) possono essere consultati e modificati
            nella pagina dedicata alla configurazione.
          </p>
        </div>

        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/config')}>
            ⚙️&nbsp; Configura i parametri fisici ed economici del modello
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
