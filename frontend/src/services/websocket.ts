import { WSEvent } from '../types'

type EventHandler = (event: WSEvent) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private handlers: Set<EventHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnecting = false

  connect(url: string = `ws://${window.location.host}/ws/stream`): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.isConnecting) {
        resolve()
        return
      }

      this.isConnecting = true

      try {
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          this.isConnecting = false
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as WSEvent
            this.handlers.forEach((handler) => handler(data))
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e)
          }
        }

        this.ws.onclose = () => {
          console.log('WebSocket disconnected')
          this.isConnecting = false
          this.attemptReconnect(url)
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.isConnecting = false
          reject(error)
        }
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  private attemptReconnect(url: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    
    setTimeout(() => {
      this.connect(url).catch(console.error)
    }, delay)
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  send(event: WSEvent) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(event))
    } else {
      console.warn('WebSocket not connected, cannot send:', event)
    }
  }

  startAnalysis(researchGoal: string) {
    this.send({ type: 'start_analysis', data: { research_goal: researchGoal } })
  }

  approveStep(stepId: string, iterationId: string) {
    this.send({ type: 'approve_step', data: { step_id: stepId, iteration_id: iterationId } })
  }

  refineStep(stepId: string, iterationId: string, feedback: string) {
    this.send({ type: 'refine_step', data: { step_id: stepId, iteration_id: iterationId, feedback } })
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsService = new WebSocketService()
