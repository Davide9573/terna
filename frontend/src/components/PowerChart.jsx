import { useMemo } from 'react'
import Plot from 'react-plotly.js'

const SOURCE_COLORS = {
  'Net Import':       '#6600FF',
  'Thermal':          '#B22222',
  'Nuclear':          '#0055FF',
  'Storage':          '#FFA500',
  'Self-consumption': '#808080',
  'Hydro':            '#87CEEB',
  'Wind':             '#4CAF50',
  'Geothermal':       '#8B4513',
  'Photovoltaic':     '#FFD700',
}

const SOURCES = [
  'Net Import', 'Thermal', 'Nuclear', 'Storage',
  'Self-consumption', 'Photovoltaic', 'Hydro', 'Wind', 'Geothermal',
]

const LINE_COLORS = {
  Import:       '#0000CC',
  Export:       '#CC0000',
  Consumption:  '#111111',
}

export default function PowerChart({ chartData, title }) {
  // Reconstruct timestamps from start + step
  const timestamps = useMemo(() => {
    const t0 = new Date(chartData.start).getTime()
    const stepMs = chartData.step_minutes * 60_000
    return Array.from({ length: chartData.n }, (_, i) =>
      new Date(t0 + i * stepMs).toISOString()
    )
  }, [chartData.start, chartData.n, chartData.step_minutes])

  const traces = useMemo(() => {
    const { series } = chartData

    // Stacked area — one trace per source present in data with non-zero values
    const stacked = SOURCES
      .filter(s => series[s]?.some(v => v > 0.0005))
      .map(s => ({
        x: timestamps,
        y: series[s],
        name: s,
        type: 'scatter',
        mode: 'none',
        stackgroup: 'gen',
        fillcolor: SOURCE_COLORS[s],
        line: { color: SOURCE_COLORS[s] },
        hovertemplate: `<b>${s}</b>: %{y:.2f} GW<extra></extra>`,
      }))

    // Overlay lines
    const overlays = ['Consumption', 'Import', 'Export']
      .filter(k => series[k])
      .map(k => ({
        x: timestamps,
        y: k === 'Export' ? series[k].map(v => -v) : series[k],
        name: k === 'Export' ? 'Export (−)' : k,
        type: 'scatter',
        mode: 'lines',
        line: { color: LINE_COLORS[k] ?? '#555', width: 1.8 },
        hovertemplate: `<b>${k}</b>: %{y:.2f} GW<extra></extra>`,
      }))

    return [...stacked, ...overlays]
  }, [chartData, timestamps])

  const layout = {
    title: { text: title, font: { size: 14, color: '#0d1b2a' } },
    xaxis: { type: 'date', title: '' },
    yaxis: { title: 'Potenza (GW)', fixedrange: false },
    hovermode: 'x unified',
    legend: {
      orientation: 'v',
      x: 1.01, xanchor: 'left', y: 1,
      font: { size: 11 },
    },
    margin: { l: 65, r: 160, t: 50, b: 55 },
    autosize: true,
    plot_bgcolor: '#fafbfc',
    paper_bgcolor: '#ffffff',
  }

  return (
    <div style={{ width: '100%' }}>
      <Plot
        data={traces}
        layout={layout}
        useResizeHandler
        style={{ width: '100%', height: '460px' }}
        config={{ scrollZoom: true, responsive: true, displaylogo: false }}
      />
    </div>
  )
}
