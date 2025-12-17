import { ReactNode, useEffect, useRef, useState } from 'react'
import { DemoIdentity } from '../types'
import { Wifi, WifiOff, ChevronDown, Cpu } from 'lucide-react'

type TabKey = 'dashboard' | 'investigation' | 'fleet' | 'reports'

interface TechOpsShellProps {
  isConnected: boolean
  model?: string | null
  identity: DemoIdentity | null
  activeTab: TabKey
  summaryLevel: 'station' | 'region' | 'company'
  onSummaryLevelChange: (level: 'station' | 'region' | 'company') => void
  onTabChange: (tab: TabKey) => void
  onSwitchIdentity?: () => void
  children: ReactNode
}

export function TechOpsShell({
  isConnected,
  model,
  identity,
  activeTab,
  summaryLevel,
  onSummaryLevelChange,
  onTabChange,
  onSwitchIdentity,
  children,
}: TechOpsShellProps) {
  const [logoFailed, setLogoFailed] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!menuRef.current) return
      if (menuRef.current.contains(e.target as Node)) return
      setMenuOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [])

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="h-16 bg-[#0B2A55] text-white border-b border-black/20 flex items-center justify-between px-6 flex-shrink-0 no-print">
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
            {([
              ['dashboard', 'Dashboard'],
              ['investigation', 'Investigation'],
              ['fleet', 'Fleet Status'],
              ['reports', 'Reports'],
            ] as const).map(([key, label]) => {
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

          {model ? (
            <div className="hidden lg:flex items-center gap-2 text-xs bg-white/10 px-3 py-1.5 rounded-full">
              <Cpu className="w-3.5 h-3.5 text-white/80" />
              <span className="text-white/80">Model:</span>
              <span className="font-semibold text-white">{model}</span>
            </div>
          ) : null}

          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/15 transition-colors px-3 py-2 rounded-lg"
              title="User menu"
              type="button"
            >
              <div className="h-8 w-8 rounded-full bg-white/15 flex items-center justify-center font-bold text-sm">
                {identity?.name?.split(' ').slice(0, 2).map((s) => s[0]).join('') || 'U'}
              </div>
              <div className="hidden lg:flex flex-col items-start leading-tight">
                <div className="text-sm font-semibold">{identity?.name || 'Loading...'}</div>
                <div className="text-xs text-white/70">
                  {identity?.role || '-'} {identity?.station ? `(${identity.station})` : ''}
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-white/70" />
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-slate-100">
                  <div className="text-xs font-extrabold text-slate-500">SUMMARIZATION</div>
                  <div className="text-sm font-semibold text-slate-900 mt-1">
                    {summaryLevel === 'station' ? 'Station' : summaryLevel === 'region' ? 'Region' : 'Company Wide'}
                  </div>
                </div>
                <div className="p-2">
                  {([
                    ['station', 'Station'],
                    ['region', 'Region'],
                    ['company', 'Company Wide'],
                  ] as const).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => {
                        onSummaryLevelChange(key)
                        setMenuOpen(false)
                      }}
                      className={[
                        'w-full text-left px-3 py-2 rounded-lg text-sm font-semibold transition-colors',
                        summaryLevel === key ? 'bg-slate-100 text-slate-900' : 'text-slate-700 hover:bg-slate-50',
                      ].join(' ')}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <div className="border-t border-slate-100 p-2">
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false)
                      onSwitchIdentity?.()
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    Switch Demo Identity
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}
