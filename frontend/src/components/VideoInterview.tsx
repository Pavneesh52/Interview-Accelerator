"use client"

import { useEffect, useRef, useState } from "react"
import { Room, Track, createLocalTracks } from "livekit-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Video, VideoOff, Mic, MicOff, Settings, X, User } from "lucide-react"

interface VideoInterviewProps {
  interviewId: string
  sessionId: string
  candidateName: string
  onLeave?: () => void
}

interface ParticipantWithTracks {
  identity: string
  isLocal: boolean
  videoTrack?: Track
  audioTrack?: Track
}

export function VideoInterview({ interviewId, sessionId, candidateName, onLeave }: VideoInterviewProps) {
  const [tokenData, setTokenData] = useState<{ token: string; url: string; roomName: string } | null>(null)
  const [connecting, setConnecting] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [localVideoOn, setLocalVideoOn] = useState(true)
  const [localAudioOn, setLocalAudioOn] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [connected, setConnected] = useState(false)
  const [participants, setParticipants] = useState<ParticipantWithTracks[]>([])
  const roomRef = useRef<Room | null>(null)

  const fetchToken = async () => {
    try {
      const response = await fetch(`/api/video/interviews/${interviewId}/video-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      if (!response.ok) throw new Error("Failed to get video token")
      const data = await response.json()
      setTokenData(data)
    } catch (err) {
      setError("Failed to connect to video service")
      console.error(err)
    } finally {
      setConnecting(false)
    }
  }

  useEffect(() => {
    fetchToken()
  }, [interviewId])

  if (connecting) {
    return (
      <Card className="w-full h-[400px]">
        <CardContent className="flex items-center justify-center h-full">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  if (error || !tokenData) {
    return (
      <Card className="w-full h-[400px] border-destructive">
        <CardContent className="flex items-center justify-center h-full text-center">
          <div>
            <VideoOff className="mx-auto h-12 w-12 text-destructive mb-4" />
            <p className="text-destructive">Unable to start video interview</p>
            <p className="text-sm text-muted-foreground mt-1">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const room = new Room({
    adaptiveStream: true,
    dynacast: true,
  })
  roomRef.current = room

  useEffect(() => {
    if (!tokenData) return

    const setupRoom = async () => {
      room.on("connected", () => {
        setConnected(true)
        updateParticipants()
      })

      room.on("participantConnected", () => {
        updateParticipants()
      })

      room.on("participantDisconnected", () => {
        updateParticipants()
      })

      room.on("trackSubscribed", () => {
        updateParticipants()
      })

      try {
        await room.connect(tokenData.url, tokenData.token)
        
        const tracks = await createLocalTracks({
          audio: true,
          video: { resolution: "720p" as any },
        })
        
        for (const track of tracks) {
          await room.localParticipant.publishTrack(track)
        }
        
        updateParticipants()
        
      } catch (err) {
        console.error("Failed to connect:", err)
      }
    }

    const updateParticipants = () => {
      const list: ParticipantWithTracks[] = []
      
      if (room.localParticipant) {
        const videoPub = room.localParticipant.getTrackPublication(Track.Source.Camera)
        const audioPub = room.localParticipant.getTrackPublication(Track.Source.Microphone)
        list.push({
          identity: room.localParticipant.identity,
          isLocal: true,
          videoTrack: videoPub?.track,
          audioTrack: audioPub?.track,
        })
      }
      
      room.remoteParticipants.forEach((participant) => {
        const videoPub = participant.getTrackPublication(Track.Source.Camera)
        const audioPub = participant.getTrackPublication(Track.Source.Microphone)
        list.push({
          identity: participant.identity,
          isLocal: false,
          videoTrack: videoPub?.track,
          audioTrack: audioPub?.track,
        })
      })
      
      setParticipants(list)
    }

    setupRoom()

    return () => {
      room.disconnect()
    }
  }, [tokenData])

  const toggleVideo = async () => {
    if (roomRef.current?.localParticipant) {
      const newState = !localVideoOn
      await roomRef.current.localParticipant.setCameraEnabled(newState)
      setLocalVideoOn(newState)
    }
  }

  const toggleAudio = async () => {
    if (roomRef.current?.localParticipant) {
      const newState = !localAudioOn
      await roomRef.current.localParticipant.setMicrophoneEnabled(newState)
      setLocalAudioOn(newState)
    }
  }

  const handleLeave = async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect()
    }
    onLeave?.()
  }

  return (
    <div className="relative w-full h-[500px] bg-muted rounded-lg overflow-hidden">
      {!connected && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted z-10">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      )}

      <div className="relative w-full h-full grid grid-cols-2 gap-2 p-2">
        {participants.map((p) => (
          <ParticipantVideo key={p.identity} participant={p} />
        ))}
      </div>

      <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between p-4 bg-background/95 backdrop-blur-sm rounded-lg shadow-lg">
        <div className="flex items-center gap-2">
          <Button
            variant={localVideoOn ? "default" : "secondary"}
            size="icon"
            onClick={toggleVideo}
            className="h-10 w-10"
          >
            {localVideoOn ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
          </Button>
          <Button
            variant={localAudioOn ? "default" : "secondary"}
            size="icon"
            onClick={toggleAudio}
            className="h-10 w-10"
          >
            {localAudioOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <User className="h-4 w-4" />
          <span className="text-sm font-medium">{candidateName}</span>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={() => setShowSettings(!showSettings)}>
            <Settings className="h-5 w-5" />
          </Button>
          <Button variant="destructive" size="icon" onClick={handleLeave}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {showSettings && (
        <div className="absolute top-4 right-4 z-10">
          <Card className="w-64 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <div className="flex items-center justify-between">
                <span className="text-sm">Camera</span>
                <Button variant="outline" size="sm" onClick={toggleVideo}>
                  {localVideoOn ? "On" : "Off"}
                </Button>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Microphone</span>
                <Button variant="outline" size="sm" onClick={toggleAudio}>
                  {localAudioOn ? "On" : "Off"}
                </Button>
              </div>
              <Button variant="outline" size="sm" className="w-full" onClick={handleLeave}>
                Leave Interview
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

function ParticipantVideo({ participant }: { participant: { identity: string; isLocal: boolean; videoTrack?: Track; audioTrack?: Track } }) {
  const { videoTrack, audioTrack, identity, isLocal } = participant
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current && videoTrack) {
      if (videoTrack instanceof MediaStreamTrack) {
        videoRef.current.srcObject = new MediaStream([videoTrack])
      }
    } else if (videoRef.current && !videoTrack) {
      videoRef.current.srcObject = null
    }
  }, [videoTrack])

  return (
    <div className="relative bg-muted rounded-lg overflow-hidden min-h-[200px]">
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        autoPlay
        playsInline
        muted={isLocal}
      />
      {!videoTrack && (
        <div className="w-full h-full flex items-center justify-center bg-muted">
          <Video className="h-16 w-16 text-muted-foreground" />
        </div>
      )}
      <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between px-2">
        <span className="text-xs bg-black/50 text-white px-2 py-1 rounded">
          {identity}
        </span>
        <div className="flex items-center gap-1">
          {audioTrack && (
            <span className="text-xs bg-black/50 text-white px-2 py-1 rounded flex items-center gap-1">
              <Mic className="h-3 w-3" />
              Live
            </span>
          )}
        </div>
      </div>
    </div>
  )
}