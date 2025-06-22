import { LiveKitRoom } from '@livekit/components-react'
import '@livekit/components-styles'
import { useState, useCallback, useEffect } from 'react'
import './App.css'
import { TokenGenerator } from './components/TokenGenerator'
import { VoiceAssistant } from './components/VoiceAssistant'

const serverUrl = import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880'

function App() {
  const [roomName, setRoomName] = useState('')
  const [participantName] = useState(() => `web-user-${Date.now()}`)
  const [connected, setConnected] = useState(false)
  const [token, setToken] = useState<string>('')
  const [key, setKey] = useState(0)

  const handleTokenGenerated = useCallback((newToken: string) => {
    setToken(newToken)
  }, [])

  const handleConnect = useCallback(() => {
    // Generate new room name for each connection
    const newRoomName = `agent-room-${Date.now()}`
    setRoomName(newRoomName)
    setConnected(true)
  }, [])

  const handleDisconnect = useCallback(() => {
    setConnected(false)
    setToken('')
    setRoomName('')
    // Force re-render of TokenGenerator to generate new token
    setKey(prev => prev + 1)
  }, [])

  useEffect(() => {
    // Reset connection state when unmounting
    return () => {
      setConnected(false)
      setToken('')
    }
  }, [])

  return (
    <div className="App">
      <h1>LiveKit Agent Web Client</h1>
      
      {!connected && (
        <div className="connect-section">
          <button 
            onClick={handleConnect}
          >
            Connect to Agent
          </button>
        </div>
      )}

      {connected && !token && (
        <div className="connect-section">
          <TokenGenerator 
            key={key}
            roomName={roomName}
            participantName={participantName}
            onTokenGenerated={handleTokenGenerated}
          />
          <p>Generating token for room: {roomName}</p>
        </div>
      )}

      {connected && token && (
        <LiveKitRoom
          video={false}
          audio={true}
          token={token}
          serverUrl={serverUrl}
          onDisconnected={handleDisconnect}
          data-lk-theme="default"
          style={{ height: '100vh' }}
        >
          <VoiceAssistant />
        </LiveKitRoom>
      )}
    </div>
  )
}

export default App
