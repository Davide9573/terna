import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Plot from 'react-plotly.js'
import DecarbonizationSurface from '../components/DecarbonizationSurface'

export default function CostAnalysisPage() {
  const navigate = useNavigate()
  const [surface, setSurface] = useState(null)
  const [nuclearSurface, setNuclearSurface] = useState(null)
  const hasLoadedInitialCosts = useRef(false)
  const [ranges, setRanges] = useState({
    k_pv_range: 20,
    k_w_range: 20,
    storage_capacity_range_twh: 20,
  })
  const [costs, setCosts] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const calculateCosts = () => {
    setLoading(true)
    setError(null)
    const requestBody = {
      k_pv_range: Number(ranges.k_pv_range),
      k_w_range: Number(ranges.k_w_range),
    }
    const storageSurfaceRequest = fetch('/api/decarbonization-surface', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...requestBody,
        storage_capacity_range_twh: Number(ranges.storage_capacity_range_twh),
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
    const nuclearSurfaceRequest = fetch('/api/nuclear-decarbonization-surface', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
    const costComparisonRequest = fetch('/api/conclusions-cost-comparison', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...requestBody,
        storage_capacity_range_twh: Number(ranges.storage_capacity_range_twh),
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })

    Promise.all([storageSurfaceRequest, nuclearSurfaceRequest, costComparisonRequest])
      .then(([storageSurface, nuclearSurface, costComparison]) => {
        setSurface(storageSurface.points)
        setNuclearSurface(nuclearSurface.points)
        setCosts(costComparison)
        setLoading(false)
      })
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
          <p>
            Lo scopo di questa sezione è analizzare quali sono i possibili scenari in grado
            di decarbonizzare la produzione elettrica italiana, <b>con e senza ricorso al nucleare</b>,
            e confrontarne i costi. <br />

            I possibili scenari "a emissioni zero" sono tanti, come tanti sono i possibili mix di fonti
            energetiche e di capacità di accumulo che si possono perseguire.
            
            Il calcolo qui effettuato esegue una serie di simulazioni di scenario (analoghe a quelle che si
            possono eseguire nella sezione precedente) esplorando, in un intervallo definito dall'utente,
            le combinazioni dei due parametri principali che definiscono la quantità di fonti rinnovabili
            del mix energetico: <br />
            - il moltiplicatore della potenza nominale di fotovoltaico, rispetto all'attualmente installato (k_pv),<br />
            - il moltiplicatore della potenza nominale di eolico, rispetto all'attualmente installato (k_w).<br />
            Le simulazioni eseguite sono due per ciascuna coppia (k_pv, k_w): una con e una senza ricorso al nucleare.
            Il risultato di queste simulazioni sono due superfici nello spazio dei parametri:<br />
            - nel primo caso, <b>senza ricorso al nucleare</b>, lo spazio dei parametri include la capacità di accumulo,
            e la superficie riportata è quella che delimita gli scenari a emissioni zero, dove è possibile annullare
            il ricorso alle fonti fossili, a costo di avere sufficiente capacità di accumulo <br />
            - nel secondo caso, <b>con ricorso al nucleare</b>, lo spazio dei parametri include la potenza nucleare richiesta,
            e la superficie riportata è quella che delimita gli scenari a emissioni zero, dove cioè è possibile annullare
            il ricorso alle fonti fossili, a costo di avere sufficiente potenza nucleare installata. <br />
            In entrambi i casi, il colore della superficie indica il costo livellato complessivo dello scenario,
            in miliardi di euro l'anno (si veda la legenda accanto).
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
            Attenzione: il ricalcolo può impiegare diversi secondi, a seconda dell'intervallo dei parametri selezionato.
          </p>
          <div className="actions-row">
            <button className="btn btn-primary" onClick={calculateCosts} disabled={loading}>
              {loading ? 'Calcolo in corso...' : 'Ricalcola superficie e costi'}
            </button>
          </div>
        </section>

        <section className="results-section">
          <h2>Superficie di decarbonizzazione escludendo il nucleare</h2>
          <p>
            Il grafico seguente fornisce una rappresentazione della superficie di decarbonizzazione
            nello spazio dei parametri k_pv, k_w e capacità di accumulo, ovvero la superficie
            che delimita gli scenari a emissioni zero, in cui è possibile annullare il ricorso alle fonti fossili
            senza ricorrere al nucleare.
            Il colore della superficie indica il costo livellato complessivo dello scenario, da confrontare con
            la legenda accanto, in miliardi di euro l'anno.
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
          <h2>Commento al grafico</h2>
          <p>
            Innanzitutto è bene sottolineare che, sebbene la quantità di energia elettrica prodotta
            da fonti fossili (circa 130TWh l'anno) sia significativamente inferiore al fabbisogno
            italiano (circa 310TWh l'anno), la quantità di energia da fonti rinnovabili necessaria
            a sopperire l'eliminazione della produzione fossile, in assenza di una fonte controllabile
            come il nucleare, dovrebbe essere incrementata in modo significativo, anche di svariati ordini
            di grandezza.
            Il che implica che una porzione importante dell'energia prodotta
            verrebbe sprecata (ciò che in gergo tecnico è chiamato "curtailment").

            Ciò è dovuto al fatto che fotovoltaico ed eolico sono fonti intermittenti e non programmabili,
            e quindi la loro produzione non può essere controllata in funzione della domanda.

            Il ricorso ad accumulatori di energia, anche tralasciando il fattore costi, può mitigare
            solo in parte questo problema, principalmente nel ciclo diurno-notturno.

            Il problema vero è che ci sono giornate con scarsissima produzione rinnovabile, per le quali
            la quantità di potenza nominale installata, necessaria a ricaricare gli accumulatori per
            far fronte alla notte, sarebbe comunque enorme.
          </p>
          <p>
            Se, viceversa, si volesse contenere la potenza rinnovabile installata (diciamo moltiplicare
            la potenza nominale attuale "solamente" per un fattore 5-10, che produrrebbe comunque una
            quantità di energia ben superiore al fabbisogno), la capacità di accumulo richiesta al fine di
            fare fronte ai lunghi periodi di scarsa disponibilità -come può capitare in giornate o
            settimane invernali con scarsa illuminazione e/o ventilazione- diventerebbe enorme.
          </p>
          <p>
            Il grafico consente di farsi un'idea precisa dell'ordine di grandezza della capacità
            di accumulo richiesta in assenza di nucleare: la superficie di decarbonizzazione presenta
            un picco asintotico di tale capacità per valori contenuti della potenza nominale di
            rinnovabili, e decresce lentamente per valori più elevati, rimanendo comunque superiore
            ad un plateau di circa 500 GWh. <br />
            A tal proposito si consideri che la capacità nominale di accumulo idroelettrico
            attualmente installata in Italia è di circa 53 GWh, un decimo appena della capacità
            richiesta da uno scenario di decarbonizzazione mediante sole rinnovabili, scenario
            che richiederebbe comunque di moltiplicare la potenza nominale fotovoltaica ed eolica
            di 20 volte ciascuna!
          </p>
        </section>

        <section className="results-section">
          <h2>Superficie di decarbonizzazione includendo il nucleare</h2>
          <p>
            Il grafico seguente esplora le stesse combinazioni di potenza fotovoltaica ed eolica,
            sostituendo la produzione termica residua con il nucleare.
            L'asse verticale indica la potenza nucleare richiesta, in GW;
            il colore rappresenta il costo livellato complessivo dello scenario,
            in miliardi di euro l'anno.
          </p>
          {loading && (
            <div className="loading-box surface-loading">
              <div className="spinner" />
              <p>Calcolo della superficie con opzione nucleare in corso...</p>
            </div>
          )}
          {error && (
            <div className="error-box">
              <strong>Errore durante il calcolo della superficie nucleare:</strong> {error}
            </div>
          )}
          {nuclearSurface && nuclearSurface.length > 0 && (
            <DecarbonizationSurface
              points={nuclearSurface}
              verticalField="nuclear_peak"
              verticalScale={1}
              verticalAxisLabel="potenza nucleare richiesta (GW)"
              verticalHoverLabel="Potenza nucleare"
              verticalHoverUnit="GW"
            />
          )}
          {nuclearSurface && nuclearSurface.length === 0 && (
            <p className="results-description-placeholder">
              Non sono stati trovati scenari con opzione nucleare nell'intervallo analizzato.
            </p>
          )}
          <h2>Commento al grafico</h2>
          <p>
            Nel caso si accettasse di utilizzare il nucleare in combinazione con le rinnovabili,
            si può notare immediatamente come non esisterebbero impedimenti tecnici a decarbonizzare
            la produzione elettrica con qualsiasi combinazione di potenza fotovoltaica ed eolica,
            a patto di installare una potenza nucleare adeguata, tale da garantire picchi di fabbisogno
            di circa 34 GW.
          </p>
          <p>
            È interessante notare anche come l'introduzione del nucleare riduca significativamente
            la necessità di aumentare la potenza rinnovabile installata (e di accumulo, non indicato
            in figura).
            
            Una variazione della potenza eolica ridurrebbe la potenza nucleare richiesta, anche se non
            in modo drammatico (da 34 GW a 26 GW, aumentando di un fattore 20 la potenza eolica).
            
            Viceversa, un incremento della potenza fotovoltaica modificherebbe in modo del tutto
            impercettibile la potenza nucleare richiesta, a causa dell'enorme variabilità stagionale
            di illuminazione solare.
            
            Lo si può notare dalla pendenza della superficie, che indica come la potenza nucleare
            richiesta sia più sensibile alla variazione della potenza eolica che a quella fotovoltaica.
          </p>
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

        <section className="results-section conclusions-section">
          <div className="conclusions-text">
            <h2>Conclusioni</h2>
            <p>
              Le simulazioni eseguite presentano una serie di approssimazioni grossolane,
              ma consentono di trarre alcune conclusioni di carattere generale, che possono essere utili
              per orientare le scelte di politica energetica in ottica di decarbonizzazione, cioè
              di rinuncia totale ai combustibili fossili.
            </p>
            <p>
              La prima considerazione è che decarbonizzare la produzione elettrica italiana con sole
              fonti rinnovabili richiederebbe: <br />
              - ingenti quantità di energia elettrica prodotta, che verrebbe in gran parte sprecata, <br />
              - ingente capacità di accumulo, attualmente non disponibile. <br />
              La presente analisi non tiene conto: <br />
              - né della realizzabilità tecnica di una simile capacità di accumulo
              (parliamo di una capacità di 1-2 ordini di grandezza superiore a quella teoricamente
              disponibile tramite pompaggio idroelettrico) <br />
              - né della complessità tecnico-economica di un sistema di trasformazione di simili quantità
              di energia da corrente continua a corrente alternata (e dissipazione dell'energia inutilizzata) <br />
              - né della fattibilità tecnica del bilanciamento della rete elettrica in
              assenza di rotori elettromeccanici di grande inerzia, come quelli presenti in centrali
              termoelettriche <br />
              - né della complessità tecnico-economica di un sistema di trasmissione e distribuzione in grado di
              gestire simili flussi energetici dalle zone di produzione a quelle di consumo. <br />
              Quindi la <b>fattibilità tecnica di una decarbonizzazione con sole rinnovabili</b> rimane
              questione <b>incerta e dibattuta</b>, ben al di là degli scopi (e delle possibilità) di questa analisi.
            </p>
            <p>
              La seconda considerazione riguarda invece il <b>confronto tra i costi</b> della decarbonizzazione
              con e senza ricorso al nucleare, anche nell'ipotesi di fattibilità tecnica di entrambe
              le soluzioni.
              
              È infatti su questo che si è focalizzato il dibattito negli ultimi mesi, ed è su questo che
              la presente analisi si concentra. <br />
              
              Il confronto dei costi complessivi (costi che l'utente può ricalcolare utilizzando
              parametri tecnico-economici personalizzati, differenti da quelli qui impostati come default)
              mostra che:<br />
              - sebbene il nucleare richieda investimenti iniziali significativi, che verrebbero ammortizzati in tempi molto lunghi, <br />
              - nonostante i costi livellati annui delle rinnovabili siano decisamente più bassi di quelli
              del nucleare, <br />
              la sua introduzione consentirebbe di ridurre significativamente i costi complessivi della
              decarbonizzazione.
              
              O meglio ancora:<br />
              l'introduzione
              del <b>nucleare appare l'unico modo per contenere i costi della decarbonizzazione</b> entro
              limiti ragionevoli, senza dover ricorrere a quantità di energia prodotta e accumulata enormi,
              e quindi a sprechi energetici e costi di gestione della rete elettrica altrettanto enormi.
            </p>
          </div>
        </section>
      </main>
    </div>
  )
}

function LevelizedCostTable({ costs }) {
  const sources = Object.keys(costs.reference)
  const scenarios = [
    { label: 'Attuale (2025)', value: costs.reference.Total, color: '#606060' },
    { label: 'Solo rinnovabili', value: costs.without_nuclear.Total, color: '#4CAF50' },
    { label: 'Mix nucleare-rinnovabili', value: costs.with_nuclear.Total, color: '#0055FF' },
  ]

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
      <Plot
        data={[{
          type: 'bar',
          x: scenarios.map(scenario => scenario.label),
          y: scenarios.map(scenario => scenario.value),
          marker: { color: scenarios.map(scenario => scenario.color) },
          hovertemplate: '%{x}<br><b>%{y:.3f} G€/anno</b><extra></extra>',
        }]}
        layout={{
          title: { text: 'Confronto del costo livellato totale', font: { size: 14, color: '#0d1b2a' } },
          yaxis: { title: 'Costo livellato (G€/anno)', rangemode: 'tozero' },
          margin: { l: 70, r: 20, t: 55, b: 90 },
          paper_bgcolor: '#ffffff',
          plot_bgcolor: '#fafbfc',
          showlegend: false,
        }}
        useResizeHandler
        style={{ width: '100%', height: '380px' }}
        config={{ responsive: true, displaylogo: false }}
      />
    </div>
  )
}
