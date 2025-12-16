import { ReactNode, useState } from 'react'
import { DemoIdentity } from '../types'
import { Wifi, WifiOff, ChevronDown } from 'lucide-react'

type TabKey = 'dashboard' | 'investigation' | 'fleet' | 'reports'

interface TechOpsShellProps {
  isConnected: boolean
  identity: DemoIdentity | null
  activeTab: TabKey
  onTabChange: (tab: TabKey) => void
  onSwitchIdentity?: () => void
  children: ReactNode
}

export function TechOpsShell({
  isConnected,
  identity,
  activeTab,
  onTabChange,
  onSwitchIdentity,
  children,
}: TechOpsShellProps) {
  const [logoFailed, setLogoFailed] = useState(false)

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="h-16 bg-[#0B2A55] text-white border-b border-black/20 flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            {!logoFailed ? (
              <img
                src="/src/assets/branding/techops-logo.png"
                alt="Southwest Tech Ops"
                className="h-10 w-auto"
                onError={() => setLogoFailed(true)}
              />
            ) : (
              <div className="flex flex-col leading-tight">
                <div className="text-lg font-extrabold tracking-tight">Southwest</div>
                <div className="text-sm font-extrabold text-[#CA8A04] -mt-1">Tech Ops</div>
              </div>
            )}
          </div>

          <nav className="hidden md:flex items-center gap-1 ml-4">
            {[
              ['dashboard', 'Dashboard'],
              ['investigation', 'Investigation'],
              ['fleet', 'Fleet Status'],
              ['reports', 'Reports'],
            ].map(([key, label]) => {
              const k = key as TabKey
              const isActive = activeTab === k
              return (
                <button
                  key={key}
                  onClick={() => onTabChange(k)}
                  className={[
                    'px-3 py-2 rounded-lg text-sm font-semibold transition-colors',
                    isActive ? 'bg-white/10 text-white' : 'text-white/80 hover:text-white hover:bg-white/10',
                  ].join(' ')}
                >
                  {label}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-sm">
            {isConnected ? (
              <>
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_3px_rgba(52,211,153,0.15)]" />
                <Wifi className="w-4 h-4 text-emerald-300" />
                <span className="text-white/80">Online</span>
              </>
            ) : (
              <>
                <span className="inline-block h-2 w-2 rounded-full bg-rose-400" />
                <WifiOff className="w-4 h-4 text-rose-300" />
                <span className="text-white/80">Offline</span>
              </>
            )}
          </div>

          <button
            onClick={onSwitchIdentity}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/15 transition-colors px-3 py-2 rounded-lg"
            title="Switch demo identity"
          >
            <div className="h-8 w-8 rounded-full bg-white/15 flex items-center justify-center font-bold text-sm">
              {identity?.name?.split(' ').slice(0, 2).map((s) => s[0]).join('') || 'U'}
            </div>
            <div className="hidden lg:flex flex-col items-start leading-tight">
              <div className="text-sm font-semibold">{identity?.name || 'Loading…'}</div>
              <div className="text-xs text-white/70">
                {identity?.role || '—'} {identity?.station ? `(${identity.station})` : ''}
              </div>
            </div>
            <ChevronDown className="w-4 h-4 text-white/70" />
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}


