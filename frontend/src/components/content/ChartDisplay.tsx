import { useState } from 'react'
import Plot from 'react-plotly.js'
import { Download, Maximize2, X } from 'lucide-react'
import { ChartSpec } from '../../types'

interface ChartDisplayProps {
  chart: ChartSpec
}

export function ChartDisplay({ chart }: ChartDisplayProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)

  const handleDownload = () => {
    // Plotly has built-in download functionality
    const plotElement = document.querySelector('.js-plotly-plot') as any
    if (plotElement) {
      import('plotly.js').then((Plotly) => {
        Plotly.downloadImage(plotElement, {
          format: 'png',
          filename: chart.title || 'chart',
          width: 1200,
          height: 800,
        })
      })
    }
  }

  const plotConfig = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'] as any,
  }

  const plotLayout = {
    ...chart.plotly_json?.layout,
    autosize: true,
    margin: { l: 50, r: 30, t: 40, b: 50 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(248, 250, 252, 0.5)',
    font: { family: 'Inter, system-ui, sans-serif' },
  }

  const ChartContent = ({ fullscreen = false }) => (
    <div className={fullscreen ? 'w-full h-full' : 'w-full'}>
      <Plot
        data={chart.plotly_json?.data || []}
        layout={{
          ...plotLayout,
          height: fullscreen ? undefined : 400,
        }}
        config={plotConfig}
        className="w-full"
        useResizeHandler
        style={{ width: '100%', height: fullscreen ? '100%' : '400px' }}
      />
    </div>
  )

  return (
    <>
      <div className="relative rounded-lg border border-slate-200 overflow-hidden bg-white">
        {/* Toolbar */}
        <div className="absolute top-2 right-2 z-10 flex gap-1">
          <button
            onClick={() => setIsFullscreen(true)}
            className="p-2 bg-white/90 hover:bg-white rounded-md shadow-sm transition-colors"
            title="Fullscreen"
          >
            <Maximize2 className="w-4 h-4 text-slate-600" />
          </button>
          <button
            onClick={handleDownload}
            className="p-2 bg-white/90 hover:bg-white rounded-md shadow-sm transition-colors"
            title="Download PNG"
          >
            <Download className="w-4 h-4 text-slate-600" />
          </button>
        </div>

        <ChartContent />
      </div>

      {/* Fullscreen modal */}
      {isFullscreen && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-8">
          <div className="relative w-full h-full bg-white rounded-lg overflow-hidden">
            <button
              onClick={() => setIsFullscreen(false)}
              className="absolute top-4 right-4 z-10 p-2 bg-slate-100 hover:bg-slate-200 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-slate-600" />
            </button>
            <div className="w-full h-full p-4">
              <ChartContent fullscreen />
            </div>
          </div>
        </div>
      )}
    </>
  )
}
