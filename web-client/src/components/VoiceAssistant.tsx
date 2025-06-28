// https://docs.livekit.io/home/quickstarts/react/
// https://github.com/livekit/components-js/tree/main/packages/react
import {
  ControlBar,
  RoomAudioRenderer,
  useParticipants,
  useConnectionState,
  ConnectionState,
  useLocalParticipant,
} from '@livekit/components-react'
import { useEffect } from 'react'

export function VoiceAssistant() {
  const participants = useParticipants()
  const connectionState = useConnectionState()
  const localParticipant = useLocalParticipant()

  useEffect(() => {
    console.log('Connection state:', connectionState)
    console.log('Participants:', participants.length)
    console.log('Local participant:', localParticipant.localParticipant?.identity)
  }, [connectionState, participants, localParticipant])

  return (
    <div className="voice-assistant">
      <RoomAudioRenderer />
      
      <div className="assistant-status">
        <h2>Voice Assistant Status</h2>
        
        <div className="connection-status">
          <p>Connection: {connectionState}</p>
        </div>

        <div className="participants">
          <h3>Participants ({participants.length})</h3>
          {participants.map((participant) => (
            <div key={participant.sid} className="participant-info">
              <span className="participant-name">
                {participant.name || participant.identity}
                {participant.isLocal && ' (You)'}
              </span>
              <span className="participant-status">
                {participant.isSpeaking ? '🔊 Speaking' : '🔇 Silent'}
                {participant.isMicrophoneEnabled ? '' : ' (Muted)'}
              </span>
            </div>
          ))}
        </div>

        {connectionState === ConnectionState.Connected && participants.length < 2 && (
          <div className="waiting-message">
            <p>Waiting for agent to join...</p>
          </div>
        )}
      </div>

      <ControlBar 
        controls={{
          microphone: true,
          camera: false,
          chat: false,
          screenShare: false,
          leave: true,
        }}
      />
    </div>
  )
}