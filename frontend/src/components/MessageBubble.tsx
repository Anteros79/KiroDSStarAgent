import { Message } from '../types'
import { User, Bot, AlertCircle, Clock, Route } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import ChartDisplay from './ChartDisplay'
import './MessageBubble.css'

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  return (
    <div className={`message-bubble ${message.role}`}>
      <div className="message-avatar">
        {isUser ? <User size={20} /> : isSystem ? <AlertCircle size={20} /> : <Bot size={20} />}
      </div>

      <div className="message-content-wrapper">
        {!isUser && message.routing && message.routing.length > 0 && (
          <div className="message-routing">
            <Route size={14} />
            <span>Routed to: {message.routing.map(r => r.replace('_', ' ')).join(', ')}</span>
          </div>
        )}

        <div className="message-content">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {message.charts && message.charts.length > 0 && (
          <div className="message-charts">
            {message.charts.map((chart, idx) => (
              <ChartDisplay key={idx} chart={chart} />
            ))}
          </div>
        )}

        {!isUser && message.execution_time_ms && (
          <div className="message-meta">
            <Clock size={12} />
            <span>{message.execution_time_ms}ms</span>
          </div>
        )}
      </div>
    </div>
  )
}
