import { ReactNode } from 'react'
import { Header } from './Header'
import { SystemStatus } from '../../types'

interface AppShellProps {
  status: SystemStatus | null
  sidebar?: ReactNode
  children: ReactNode
}

export function AppShell({ status, sidebar, children }: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header status={status} />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - optional */}
        {sidebar && (
          <aside className="w-80 flex-shrink-0 bg-sidebar text-white overflow-y-auto scrollbar-thin">
            {sidebar}
          </aside>
        )}
        
        {/* Main content */}
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  )
}
