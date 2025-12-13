import { StreamEvent } from '../types'
import { Activity, Route, Wrench, CheckCircle } from 'lucide-react'
import './StreamingIndicator.css'

interface StreamingIndicatorProps {
  events: StreamEvent[]
}

export default function StreamingIndicator({ events }: StreamingIndicatorProps) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'agent_start':
      case 'query_start':
        return <Activity size={14} />
      case 'routing':
        return <Route size={14} />
      case 'tool_start':
      case 'tool_end':
        return <Wrench size={14} />
      case 'agent_end':
        return <CheckCircle size={14} />
      default:
        return <Activity size={14} />
    }
  }

  const getEventLabel = (event: StreamEvent) => {
    switch (event.type) {
      case 'query_start':
        return 'Processing query...'
      case 'agent_start':
        return `${event.data.agent} started`
      case 'routing':
        return `Routing to ${event.data.specialist}`
      case 'tool_start':
        return `Using tool: ${event.data.tool}`
      case 'tool_end':
        return `Tool completed: ${event.data.tool}`
      case 'agent_end':
        return `${event.data.agent} completed`
      default:
        return event.type
    }
  }

  return (
    <div className="streaming-indicator">
      <div className="streaming-header">
        <div className="streaming-pulse"></div>
        <span>Investigation in progress...</span>
      </div>
      
      <div className="streaming-events">
        {events.map((event, idx) => (
          <div key={idx} className="streaming-event">
            <div className="event-icon">{getEventIcon(event.type)}</div>
            <div className="event-content">
              <div className="event-label">{getEventLabel(event)}</div>
              {event.data.reasoning && (
                <div className="event-detail">{event.data.reasoning}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
