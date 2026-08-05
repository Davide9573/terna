import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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

    Promise.all([storageSurfaceRequest, nuclearSurfaceRequest])
      .then(([storageSurface, nuclearSurface]) => {
        setSurface(storageSurface.points)
        setNuclearSurface(nuclearSurface.points)
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
            di decarbonizzare la produzione elettrica italiana, con e senza ricorso all'energia nucleare,
            e confrontarne i costi. <br />
            I possibili scenari "a emissioni zero" sono tanti, come tanti sono i possibili mix di fonti
            energetiche e di capacità di accumulo che si possono perseguire. <br />
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
            Attenzione: il ricalcolo può impiegare alcuni minuti, a seconda dell'intervallo dei parametri selezionato.
          </p>
          <div className="actions-row">
            <button className="btn btn-primary" onClick={calculateCosts} disabled={loading}>
              {loading ? 'Calcolo in corso...' : 'Ricalcola superficie e costi'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => navigate('/conclusions', { state: { ranges } })}
            >
              Vai alle conclusioni
            </button>
          </div>
        </section>

        <section className="results-section">
          <h2>Superficie di decarbonizzazione senza ricorso al nucleare</h2>
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
          <h2>Superficie di decarbonizzazione con ricorso al nucleare</h2>
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
      </main>
    </div>
  )
}
