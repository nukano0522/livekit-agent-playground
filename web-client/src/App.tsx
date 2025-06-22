import { LiveKitRoom } from '@livekit/components-react'
import '@livekit/components-styles'
import { useState, useCallback } from 'react'
import './App.css'
import { TokenGenerator } from './components/TokenGenerator'
import { VoiceAssistant } from './components/VoiceAssistant'

const serverUrl = import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880'

function App() {
  const [roomName] = useState('agent-test-room')
  const [participantName] = useState('web-user')
  const [connected, setConnected] = useState(false)
  const [token, setToken] = useState<string>('')

  const handleTokenGenerated = useCallback((newToken: string) => {
    setToken(newToken)
  }, [])

  const handleDisconnect = useCallback(() => {
    setConnected(false)
  }, [])

  return (
    <div className="App">
      <h1>LiveKit Agent Web Client</h1>
      
      {!connected && (
        <div className="connect-section">
          <TokenGenerator 
            roomName={roomName}
            participantName={participantName}
            onTokenGenerated={handleTokenGenerated}
          />
          <button 
            onClick={() => setConnected(true)}
            disabled={!token}
          >
            {token ? 'Connect to Agent' : 'Generating token...'}
          </button>
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
