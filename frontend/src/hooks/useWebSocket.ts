import { useState, useEffect, useCallback } from 'react'
import { wsService } from '../services/websocket'
import { WSEvent } from '../types'

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const connect = async () => {
      try {
        await wsService.connect()
        setIsConnected(true)
        setError(null)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'WebSocket connection failed')
        setIsConnected(false)
      }
    }

    connect()

    // Check connection status periodically
    const interval = setInterval(() => {
      setIsConnected(wsService.isConnected)
    }, 1000)

    return () => {
      clearInterval(interval)
    }
  }, [])

  const subscribe = useCallback((handler: (event: WSEvent) => void) => {
    return wsService.subscribe(handler)
  }, [])

  const reconnect = useCallback(async () => {
    setError(null)
    try {
      await wsService.connect()
      setIsConnected(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reconnection failed')
    }
  }, [])

  return {
    isConnected,
    error,
    subscribe,
    reconnect,
  }
}
