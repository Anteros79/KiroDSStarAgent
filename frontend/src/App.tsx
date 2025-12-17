import { useEffect, useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { apiService } from './services/api'
import { SystemStatus } from './types'
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { techOpsApi } from './techops/api'
import { DemoIdentity } from './techops/types'
import { TechOpsShell } from './techops/layout/TechOpsShell'
import { DashboardPage } from './techops/pages/DashboardPage'
import { InvestigationPage } from './techops/pages/InvestigationPage'
import { FinalConclusionsPage } from './techops/pages/FinalConclusionsPage'

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const { isConnected } = useWebSocket()

  const [identity, setIdentity] = useState<DemoIdentity | null>(null)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'investigation' | 'fleet' | 'reports'>('dashboard')
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(null)
  const [investigationView, setInvestigationView] = useState<'workbench' | 'final'>('workbench')
  const [summaryLevel, setSummaryLevel] = useState<'station' | 'region' | 'company'>('station')

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

  useEffect(() => {
    techOpsApi
      .getMe()
      .then(setIdentity)
      .catch((e) => {
        console.warn('Failed to load demo identity:', e)
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

  const station = identity?.station || 'DAL'

  return (
    <TechOpsShell
      isConnected={effectiveStatus?.status === 'ready'}
      model={effectiveStatus?.model}
      identity={identity}
      activeTab={activeTab}
      summaryLevel={summaryLevel}
      onSummaryLevelChange={setSummaryLevel}
      onTabChange={(t) => {
        setActiveTab(t)
        if (t !== 'investigation') setActiveInvestigationId(null)
        if (t !== 'investigation') setInvestigationView('workbench')
      }}
      onSwitchIdentity={async () => {
        // quick cycle identities for demo
        const next = identity?.id === 'jmartinez' ? 'techops_phx' : identity?.id === 'techops_phx' ? 'reliability_hq' : 'jmartinez'
        try {
          const me = await techOpsApi.selectMe(next)
          setIdentity(me)
        } catch (e) {
          console.warn('Failed to switch identity:', e)
        }
      }}
    >
      {activeTab === 'dashboard' && (
        <DashboardPage
          station={station}
          summaryLevel={summaryLevel}
          onOpenInvestigation={async ({ kpi_id, window, point_t }) => {
            const created = await techOpsApi.createInvestigation({ kpi_id, station, window, point_t, summary_level: summaryLevel })
            setActiveInvestigationId(created.investigation_id)
            setInvestigationView('workbench')
            setActiveTab('investigation')
          }}
          onSelectInvestigation={(investigation_id) => {
            setActiveInvestigationId(investigation_id)
            setInvestigationView('workbench')
            setActiveTab('investigation')
          }}
        />
      )}

      {activeTab === 'investigation' && activeInvestigationId && investigationView === 'workbench' && (
        <InvestigationPage
          investigationId={activeInvestigationId}
          onBack={() => {
            setActiveInvestigationId(null)
            setInvestigationView('workbench')
            setActiveTab('dashboard')
          }}
          onFinalize={() => setInvestigationView('final')}
        />
      )}

      {activeTab === 'investigation' && activeInvestigationId && investigationView === 'final' && (
        <FinalConclusionsPage
          investigationId={activeInvestigationId}
          onBack={() => setInvestigationView('workbench')}
          onDone={() => {
            // after submission, return to station signal grid
            setActiveInvestigationId(null)
            setInvestigationView('workbench')
            setActiveTab('dashboard')
          }}
        />
      )}

      {activeTab === 'investigation' && !activeInvestigationId && (
        <div className="px-6 py-6">
          <div className="max-w-5xl mx-auto bg-white border border-slate-200 rounded-xl p-6 text-slate-700">
            Select a KPI on the dashboard to start a DS‑STAR investigation.
          </div>
        </div>
      )}

      {activeTab === 'fleet' && (
        <div className="px-6 py-6">
          <div className="max-w-5xl mx-auto bg-white border border-slate-200 rounded-xl p-6 text-slate-700">
            Fleet Status (coming next).
          </div>
        </div>
      )}

      {activeTab === 'reports' && (
        <div className="px-6 py-6">
          <div className="max-w-5xl mx-auto bg-white border border-slate-200 rounded-xl p-6 text-slate-700">
            Reports (coming next).
          </div>
        </div>
      )}
    </TechOpsShell>
  )
}

export default App
