import { AccessToken } from 'livekit-server-sdk'
import { useEffect, useState } from 'react'

interface TokenGeneratorProps {
  roomName: string
  participantName: string
  onTokenGenerated: (token: string) => void
}

export function TokenGenerator({ roomName, participantName, onTokenGenerated }: TokenGeneratorProps) {
  const [isGenerating, setIsGenerating] = useState(false)

  useEffect(() => {
    const generateToken = async () => {
      setIsGenerating(true)
      try {
        // In a real app, this would be done on your server
        // For development, we'll generate it client-side
        const at = new AccessToken(
          import.meta.env.VITE_LIVEKIT_API_KEY || 'devkey',
          import.meta.env.VITE_LIVEKIT_API_SECRET || 'secret',
          {
            identity: participantName,
            name: participantName,
          }
        )
        
        at.addGrant({ roomJoin: true, room: roomName })
        const token = await at.toJwt()
        onTokenGenerated(token)
      } catch (error) {
        console.error('Failed to generate token:', error)
      } finally {
        setIsGenerating(false)
      }
    }

    if (roomName && participantName) {
      generateToken()
    }
  }, [roomName, participantName, onTokenGenerated])

  if (isGenerating) {
    return <div>Generating token...</div>
  }

  return null
}