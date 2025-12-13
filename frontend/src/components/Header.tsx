import { SystemStatus } from '../types'
import { Activity, Database, Cpu } from 'lucide-react'
import './Header.css'

interface HeaderProps {
  status: SystemStatus | null
}

export default function Header({ status }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">
            <Activity size={32} />
            <div>
              <h1>DS-Star</h1>
              <p>Multi-Agent System</p>
            </div>
          </div>
        </div>
        
        {status && (
          <div className="header-right">
            <div className="status-item">
              <Cpu size={16} />
              <span>{status.model}</span>
            </div>
            <div className="status-item">
              <Database size={16} />
              <span className={status.data_loaded ? 'status-active' : 'status-inactive'}>
                {status.data_loaded ? 'Data Loaded' : 'No Data'}
              </span>
            </div>
            <div className="status-indicator">
              <div className="status-dot"></div>
              <span>Ready</span>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
