import { useNavigate } from 'react-router-dom'

export default function ConclusionsPage() {
  const navigate = useNavigate()

  return (
    <div className="page">
      <header className="app-header">
        <h1>Conclusioni</h1>
      </header>

      <main className="content">
        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/cost-analysis')}>
            ← Torna all'analisi dei costi
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/')}>
            ← Torna alla pagina principale
          </button>
        </div>
      </main>
    </div>
  )
}