import { useState, useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { InvestigationWorkbench } from './components/investigation/InvestigationWorkbench'
import { useWebSocket } from './hooks/useWebSocket'
import { apiService } from './services/api'
import { SystemStatus, DatasetInfo } from './types'
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react'

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const { isConnected } = useWebSocket()

  // Mock dataset for demo (will come from backend in production)
  const [dataset] = useState<DatasetInfo>({
    filename: 'airline_operations.csv',
    description: 'Airline operational data including flights, delays, and performance metrics',
    columns: [
      { name: 'flight_id', dtype: 'int64' },
      { name: 'airline', dtype: 'string' },
      { name: 'departure_delay', dtype: 'float64' },
      { name: 'arrival_delay', dtype: 'float64' },
      { name: 'distance', dtype: 'int64' },
      { name: 'origin', dtype: 'string' },
      { name: 'destination', dtype: 'string' },
    ],
    rowCount: 50000,
  })

  useEffect(() => {
    apiService.getStatus()
      .then((data) => {
        setStatus(data)
        setLoading(false)
      })
      .catch((err) => {
        setError('Failed to connect to DS-Star system')
        setLoading(false)
        console.error('Status fetch error:', err)
      })
  }, [])

  // Update status with connection state
  const effectiveStatus: SystemStatus | null = status 
    ? { ...status, status: isConnected ? 'ready' : 'error' }
    : null

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
        <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
        <p className="text-lg text-slate-600">Initializing DS-Star System...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
        <div className="card-elevated max-w-md text-center p-8">
          <AlertCircle className="w-16 h-16 text-error mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Connection Error</h2>
          <p className="text-slate-600 mb-4">{error}</p>
          <p className="text-sm text-slate-500 mb-6">
            Make sure the backend server is running on port 8000
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            <RefreshCw className="w-4 h-4" />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <AppShell status={effectiveStatus}>
      <InvestigationWorkbench
        measureName="On-Time Performance"
        datasetName={dataset.filename}
      />
    </AppShell>
  )
}

export default App
