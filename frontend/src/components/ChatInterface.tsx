import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import MessageList from './MessageList'
import { Message, StreamEvent } from '../types'
import './ChatInterface.css'

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentEvents, setCurrentEvents] = useState<StreamEvent[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentEvents])

  useEffect(() => {
    // Initialize WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/query`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data: StreamEvent = JSON.parse(event.data)
      
      if (data.type === 'response') {
        // Final response received
        const responseMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.data.response,
          timestamp: new Date(data.timestamp),
          routing: data.data.routing,
          execution_time_ms: data.data.execution_time_ms,
          charts: data.data.charts,
          events: currentEvents,
        }
        setMessages(prev => [...prev, responseMessage])
        setCurrentEvents([])
        setIsLoading(false)
      } else if (data.type === 'error') {
        const errorMessage: Message = {
          id: Date.now().toString(),
          role: 'system',
          content: `Error: ${data.data.message}`,
          timestamp: new Date(data.timestamp),
        }
        setMessages(prev => [...prev, errorMessage])
        setCurrentEvents([])
        setIsLoading(false)
      } else {
        // Stream event
        setCurrentEvents(prev => [...prev, data])
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsLoading(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    wsRef.current = ws

    return () => {
      ws.close()
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading || !wsRef.current) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setCurrentEvents([])

    // Send query via WebSocket
    wsRef.current.send(JSON.stringify({ query: input.trim() }))
  }

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        <MessageList messages={messages} currentEvents={currentEvents} isLoading={isLoading} />
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <div className="chat-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about airline operations..."
            className="chat-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="chat-submit"
            disabled={isLoading || !input.trim()}
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  )
}
