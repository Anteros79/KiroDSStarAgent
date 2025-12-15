import { BarChart3, Brain, Sparkles, Trash2 } from 'lucide-react'
import './Sidebar.css'

interface SidebarProps {
  specialists: string[]
}

const specialistIcons: Record<string, any> = {
  data_analyst: BarChart3,
  ml_engineer: Brain,
  visualization_expert: Sparkles,
}

const specialistNames: Record<string, string> = {
  data_analyst: 'Data Analyst',
  ml_engineer: 'ML Engineer',
  visualization_expert: 'Visualization Expert',
}

const specialistDescriptions: Record<string, string> = {
  data_analyst: 'Statistical analysis and data exploration',
  ml_engineer: 'ML recommendations and code generation',
  visualization_expert: 'Chart creation and visualization',
}

export default function Sidebar({ specialists }: SidebarProps) {
  const handleClearHistory = async () => {
    try {
      await fetch('/api/history', { method: 'DELETE' })
      window.location.reload()
    } catch (err) {
      console.error('Failed to clear history:', err)
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <h3>Available Specialists</h3>
        <div className="specialists-list">
          {specialists.map(specialist => {
            const Icon = specialistIcons[specialist] || Brain
            return (
              <div key={specialist} className="specialist-card">
                <div className="specialist-icon">
                  <Icon size={20} />
                </div>
                <div className="specialist-info">
                  <h4>{specialistNames[specialist] || specialist}</h4>
                  <p>{specialistDescriptions[specialist] || 'Specialist agent'}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="sidebar-section">
        <h3>Example Queries</h3>
        <div className="example-queries">
          <div className="example-query">
            <p>What's the average delay by airline?</p>
          </div>
          <div className="example-query">
            <p>Build a model to predict flight delays</p>
          </div>
          <div className="example-query">
            <p>Create a chart showing OTP trends</p>
          </div>
          <div className="example-query">
            <p>Analyze delays and create visualizations</p>
          </div>
        </div>
      </div>

      <div className="sidebar-actions">
        <button className="sidebar-button" onClick={handleClearHistory}>
          <Trash2 size={16} />
          Clear History
        </button>
      </div>
    </aside>
  )
}
