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

  return (
    <div className="chart-display">
      <div className="chart-header">
        <h4>{chart.title}</h4>
        <span className="chart-type">{chart.chart_type}</span>
      </div>
      <div className="chart-container">
        <Plot
          data={chart.plotly_json.data || []}
          layout={{
            ...chart.plotly_json.layout,
            paper_bgcolor: '#1e293b',
            plot_bgcolor: '#0f172a',
            font: { color: '#e2e8f0' },
            autosize: true,
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
          }}
          style={{ width: '100%', height: '400px' }}
        />
      </div>
    </div>
  )
}
