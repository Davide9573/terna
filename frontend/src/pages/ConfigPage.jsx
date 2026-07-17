import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function ConfigPage() {
  const [params, setParams] = useState([])
  const [edit, setEdit] = useState({})
  const [saving, setSaving] = useState({})
  const [saved, setSaved] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/parameters')
      .then(r => r.json())
      .then(data => {
        setParams(data)
        const v = {}
        data.forEach(p => { v[p.key] = p.current })
        setEdit(v)
      })
  }, [])

  const handleChange = (key, val) => {
    setEdit(e => ({ ...e, [key]: val }))
    setSaved(s => ({ ...s, [key]: false }))
  }

  const handleSave = async (key) => {
    setSaving(s => ({ ...s, [key]: true }))
    const res = await fetch('/api/parameters', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value: Number(edit[key]) }),
    })
    if (res.ok) {
      const updated = await res.json()
      setEdit(e => ({ ...e, [key]: updated.value }))
    }
    setSaving(s => ({ ...s, [key]: false }))
    setSaved(s => ({ ...s, [key]: true }))
    setTimeout(() => setSaved(s => ({ ...s, [key]: false })), 2500)
  }

  const handleReset = async () => {
    const data = await fetch('/api/parameters/reset', { method: 'POST' }).then(r => r.json())
    setParams(data)
    const v = {}
    data.forEach(p => { v[p.key] = p.current })
    setEdit(v)
    setSaved({})
  }

  const isDirty = (key, defaultVal) => {
    const cur = Number(edit[key])
    return !isNaN(cur) && Math.abs(cur - defaultVal) > 1e-10
  }

  return (
    <div className="page">
      <header className="app-header">
        <h1>Configurazione parametri del modello</h1>
      </header>

      <main className="content">
        <div className="actions-row">
          <button className="btn btn-secondary" onClick={() => navigate('/')}>
            ← Torna alla pagina principale
          </button>
          <button className="btn btn-danger" onClick={handleReset}>
            ↺ Ripristina valori di default
          </button>
        </div>

        {/* Explanation */}
        <div className="card">
          <h2>Come usare lo strumento</h2>
          <p>
            La tabella seguente consente di consultare e modificare i parametri fisici ed economici del modello
            (rendimenti di carica e scarica degli accumuli, costi livellati dell'energia LCOE/LCOS, costo
            dell'importazione).
          </p>
        </div>

        <div className="config-table-wrapper">
          <table className="config-table">
            <thead>
              <tr>
                <th>Parametro</th>
                <th>Valore corrente</th>
                <th>Default</th>
                <th>Unità</th>
                <th>Descrizione e fonte</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {params.map(p => (
                <tr key={p.key}>
                  <td className="param-label">
                    {p.label}
                    {isDirty(p.key, p.default) && <span className="changed-badge">modificato</span>}
                  </td>
                  <td>
                    <input
                      type="number"
                      step="any"
                      className="config-input"
                      value={edit[p.key] ?? p.current}
                      onChange={e => handleChange(p.key, e.target.value)}
                    />
                  </td>
                  <td className="default-val">{p.default}</td>
                  <td className="unit-cell">{p.unit}</td>
                  <td className="desc-cell">
                    <p>{p.description}</p>
                    <p className="rationale">{p.rationale}</p>
                  </td>
                  <td>
                    <button
                      className={`btn btn-sm ${saved[p.key] ? 'btn-success' : 'btn-primary'}`}
                      onClick={() => handleSave(p.key)}
                      disabled={saving[p.key]}
                    >
                      {saving[p.key] ? '…' : saved[p.key] ? '✓ Salvato' : 'Salva'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
