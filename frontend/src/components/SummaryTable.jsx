const SOURCES = [
  'Net Import', 'Thermal', 'Nuclear', 'Storage',
  'Self-consumption', 'Photovoltaic', 'Hydro', 'Wind', 'Geothermal',
]
const OTHER = ['Import', 'Export', 'Consumption']

export default function SummaryTable({ energy, peaks }) {
  const activeSources = SOURCES.filter(s => (energy[s] ?? 0) > 0.001)
  const activeOther   = OTHER.filter(s => (energy[s] ?? 0) > 0.001)

  const row = (s, bold = false) => (
    <tr key={s} className={bold ? 'total-row' : ''}>
      <td>{bold ? <strong>{s}</strong> : s}</td>
      <td>{bold ? <strong>{(energy[s] ?? 0).toFixed(2)}</strong> : (energy[s] ?? 0).toFixed(2)}</td>
      <td>{bold ? <strong>{(peaks[s]?.value ?? 0).toFixed(2)}</strong> : (peaks[s]?.value ?? 0).toFixed(2)}</td>
      <td>{bold ? <strong>{peaks[s]?.time ?? '—'}</strong> : peaks[s]?.time ?? '—'}</td>
    </tr>
  )

  return (
    <div className="summary-table-wrapper">
      <table className="summary-table">
        <thead>
          <tr>
            <th>Fonte</th>
            <th>Energia (TWh)</th>
            <th>Picco di potenza (GW)</th>
            <th>Data/ora del picco</th>
          </tr>
        </thead>
        <tbody>
          {activeSources.map(s => row(s))}
          <tr className="sep-row"><td colSpan={4} /></tr>
          {row('Total Production', true)}
          {row('Curtailment')}
          <tr className="sep-row"><td colSpan={4} /></tr>
          {activeOther.map(s => row(s))}
        </tbody>
      </table>
    </div>
  )
}
