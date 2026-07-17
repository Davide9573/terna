const SOURCES = [
  'Net Import', 'Thermal', 'Nuclear', 'Storage',
  'Self-consumption', 'Photovoltaic', 'Hydro', 'Wind', 'Geothermal',
]
const OTHER = ['Import', 'Export', 'Consumption']

export default function SummaryTable({ energy, peaks }) {
  const energyValue = (source) => energy[source]?.energy ?? 0
  const costValue = (source) => energy[source]?.cost ?? 0
  const activeSources = SOURCES.filter(s => energyValue(s) > 0.001)
  const activeOther   = OTHER.filter(s => energyValue(s) > 0.001)

  const row = (s, bold = false) => (
    <tr key={s} className={bold ? 'total-row' : ''}>
      <td>{bold ? <strong>{s}</strong> : s}</td>
      <td>{bold ? <strong>{energyValue(s).toFixed(2)}</strong> : energyValue(s).toFixed(2)}</td>
      <td>{bold ? <strong>{costValue(s).toFixed(2)}</strong> : costValue(s).toFixed(2)}</td>
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
            <th>Costo annuo (G€/anno)</th>
            <th>Picco di potenza (GW)</th>
            <th>Data/ora del picco</th>
          </tr>
        </thead>
        <tbody>
          {activeSources.map(s => row(s))}
          <tr className="sep-row"><td colSpan={5} /></tr>
          {row('Total Production', true)}
          {row('Curtailment')}
          <tr className="sep-row"><td colSpan={5} /></tr>
          {activeOther.map(s => row(s))}
        </tbody>
      </table>
    </div>
  )
}
