import { useMemo } from 'react'
import Plot from 'react-plotly.js'

export default function DecarbonizationSurface({ points }) {
  const traces = useMemo(() => {
    const x = points.map(point => point.k_pv)
    const y = points.map(point => point.k_w)
    const z = points.map(point => point.storage_capacity / 1000)
    const cost = points.map(point => point.cost)

    return [{
      type: 'mesh3d',
      x,
      y,
      z,
      intensity: cost,
      colorscale: 'Viridis',
      colorbar: { title: { text: 'Costo<br>G€/anno' } },
      showscale: true,
      opacity: 0.92,
      hovertemplate:
        'k_pv: %{x:.2f}x<br>' +
        'k_w: %{y:.2f}x<br>' +
        'Accumulo: %{z:.2f} TWh<br>' +
        'Costo: %{intensity:.2f} G€/anno<extra></extra>',
    }]
  }, [points])

  const layout = {
    scene: {
      xaxis: { title: { text: 'moltiplicatore potenza PV' } },
      yaxis: { title: { text: 'moltiplicatore potenza eolica' } },
      zaxis: { title: { text: 'capacità di accumulo (TWh)' } },
      camera: { eye: { x: 1.5, y: 1.5, z: 1.05 } },
    },
    margin: { l: 0, r: 0, t: 20, b: 0 },
    paper_bgcolor: '#ffffff',
  }

  return (
    <Plot
      data={traces}
      layout={layout}
      useResizeHandler
      style={{ width: '100%', height: '580px' }}
      config={{ responsive: true, displaylogo: false }}
    />
  )
}