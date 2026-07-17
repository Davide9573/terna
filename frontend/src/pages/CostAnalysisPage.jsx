import { useNavigate } from 'react-router-dom'

export default function CostAnalysisPage() {
  const navigate = useNavigate()

  return (
    <div className="page">
      <header className="app-header">
        <h1>Analisi dei costi degli scenari a emissioni zero</h1>
        <p className="subtitle">Confronta i costi di diversi scenari alternativi</p>
      </header>

      <main className="content">
        <div className="card">
          <h2>Analisi costi</h2>
          <p>Contenuto in fase di sviluppo...</p>

          <div className="actions-row">
            <button className="btn btn-secondary" onClick={() => navigate('/')}>
              ← Indietro
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
