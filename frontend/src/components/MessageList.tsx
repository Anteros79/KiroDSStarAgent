import { Message, StreamEvent } from '../types'
import MessageBubble from './MessageBubble'
import StreamingIndicator from './StreamingIndicator'
import './MessageList.css'

interface MessageListProps {
  messages: Message[]
  currentEvents: StreamEvent[]
  isLoading: boolean
}

export default function MessageList({ messages, currentEvents, isLoading }: MessageListProps) {
  return (
    <div className="message-list">
      {messages.length === 0 && !isLoading && (
        <div className="empty-state">
          <h2>Welcome to DS-Star</h2>
          <p>Ask questions about airline operations data and get insights from our specialist agents.</p>
          <div className="example-prompts">
            <p className="example-label">Try asking:</p>
            <div className="example-prompt">"What's the average delay by airline?"</div>
            <div className="example-prompt">"Build a model to predict flight delays"</div>
            <div className="example-prompt">"Create a chart showing OTP trends"</div>
          </div>
        </div>
      )}

      {messages.map(message => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isLoading && currentEvents.length > 0 && (
        <StreamingIndicator events={currentEvents} />
      )}
    </div>
  )
}
