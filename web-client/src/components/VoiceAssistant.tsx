import {
  ControlBar,
  GridLayout,
  ParticipantTile,
  RoomAudioRenderer,
  useParticipants,
  useTracks,
} from '@livekit/components-react'
import { Track } from 'livekit-client'

export function VoiceAssistant() {
  const participants = useParticipants()
  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: false },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false }
  )

  return (
    <div className="voice-assistant">
      <RoomAudioRenderer />
      
      <div className="assistant-status">
        <h2>Voice Assistant Status</h2>
        <div className="participants">
          <h3>Participants ({participants.length})</h3>
          {participants.map((participant) => (
            <div key={participant.sid} className="participant-info">
              <span className="participant-name">{participant.name || participant.identity}</span>
              <span className="participant-status">
                {participant.isSpeaking ? '🔊 Speaking' : '🔇 Silent'}
              </span>
            </div>
          ))}
        </div>
      </div>

      <GridLayout tracks={tracks} style={{ height: 'calc(100% - 150px)' }}>
        <ParticipantTile />
      </GridLayout>

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