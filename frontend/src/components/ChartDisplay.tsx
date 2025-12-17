import { ChartData } from '../types'
import Plot from 'react-plotly.js'
import './ChartDisplay.css'

interface ChartDisplayProps {
  chart: ChartData
}

export default function ChartDisplay({ chart }: ChartDisplayProps) {
  if (!chart.plotly_json) {
    return (
      <div className="chart-display">
        <div className="chart-header">
          <h4>{chart.title}</h4>
          <span className="chart-type">{chart.chart_type}</span>
        </div>
        <div className="chart-placeholder">
          <p>Chart data available but no Plotly JSON provided</p>
        </div>
      </div>
    )
  }

  const layout = chart.plotly_json.layout || {}
  const mergedLayout = {
    ...layout,
    paper_bgcolor: layout.paper_bgcolor ?? '#FFFFFF',
    plot_bgcolor: layout.plot_bgcolor ?? '#FFFFFF',
    font: layout.font ?? { family: 'Inter, system-ui, sans-serif', color: '#0f172a' },
    autosize: true,
    height: (layout as any).height ?? 520,
  }

  return (
    <div className="chart-display">
      <div className="chart-header">
        <h4>{chart.title}</h4>
        <span className="chart-type">{chart.chart_type}</span>
      </div>
      <div className="chart-container">
        <Plot
          data={chart.plotly_json.data || []}
          layout={mergedLayout as any}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            scrollZoom: true,
          }}
          style={{ width: '100%', height: '520px' }}
        />
      </div>
    </div>
  )
}
