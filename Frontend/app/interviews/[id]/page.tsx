'use client'

import React, { useState } from 'react'
import dynamic from 'next/dynamic'
import { motion } from 'framer-motion'
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Phone,
  Share2,
  MessageCircle,
  Code2,
  Maximize2,
  ChevronDown,
  Volume2,
  Signal,
  AlertCircle,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

// Dynamically import Monaco Editor
const MonacoEditor = dynamic(() => import('@monaco-editor/react').then((m) => m.default), {
  ssr: false,
  loading: () => <div className="text-center text-muted-foreground">Loading editor...</div>,
})

interface TranscriptEntry {
  speaker: string
  timestamp: string
  text: string
}

export default function InterviewRoomPage({ params }: { params: { id: string } }) {
  const [isMuted, setIsMuted] = useState(false)
  const [isCameraOff, setIsCameraOff] = useState(false)
  const [isScreenSharing, setIsScreenSharing] = useState(false)
  const [activePanel, setActivePanel] = useState<'transcript' | 'chat' | 'whiteboard'>('transcript')
  const [showChat, setShowChat] = useState(false)
  const [codeLanguage, setCodeLanguage] = useState('javascript')
  const [code, setCode] = useState(
    `// Welcome to TalentOS Interview Room
// Write your solution here

function solve(arr) {
  // Your code here
  return arr;
}`,
  )

  const [transcript, setTranscript] = useState<TranscriptEntry[]>([
    {
      speaker: 'Interviewer',
      timestamp: '00:00',
      text: 'Welcome to the interview. Can you introduce yourself?',
    },
    {
      speaker: 'Candidate',
      timestamp: '00:15',
      text: 'Hi! I am excited to be here. I have 5 years of experience in full-stack development.',
    },
    {
      speaker: 'Interviewer',
      timestamp: '00:45',
      text: 'Great! Let\'s start with the first problem. Can you solve this coding challenge?',
    },
  ])

  const [messages, setMessages] = useState<Array<{ author: string; text: string }>>([
    { author: 'System', text: 'Interview started' },
  ])

  const [messageInput, setMessageInput] = useState('')

  const sendMessage = () => {
    if (messageInput.trim()) {
      setMessages([...messages, { author: 'You', text: messageInput }])
      setMessageInput('')
    }
  }

  return (
    <div className="fixed inset-0 bg-background overflow-hidden">
      {/* Main Grid */}
      <div className="h-full flex flex-col lg:grid lg:grid-cols-4 gap-0 lg:gap-4 p-4 lg:p-6">
        {/* Video Area - Takes up 2 columns on desktop */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="lg:col-span-2 rounded-lg overflow-hidden border border-border/40 bg-black mb-4 lg:mb-0 flex flex-col h-96 lg:h-full"
        >
          {/* Video Stream */}
          <div className="flex-1 bg-gradient-to-br from-blue-primary/20 to-accent/20 flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 backdrop-blur-sm" />
            <div className="relative z-10 text-center space-y-4">
              <Avatar className="w-32 h-32 mx-auto">
                <AvatarFallback className="text-2xl">SA</AvatarFallback>
              </Avatar>
              <div>
                <p className="text-lg font-semibold text-foreground">Sarah Anderson</p>
                <p className="text-sm text-muted-foreground">Senior Full-Stack Engineer</p>
              </div>
            </div>

            {/* Connection Quality Indicator */}
            <div className="absolute top-4 left-4 z-20">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/50 backdrop-blur-sm border border-border/20">
                <Signal className="w-4 h-4 text-green-500" />
                <span className="text-xs font-medium text-foreground">Excellent</span>
              </div>
            </div>

            {/* Recording Indicator */}
            <div className="absolute top-4 right-4 z-20">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/20 backdrop-blur-sm border border-red-500/30 animate-pulse">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-xs font-medium text-red-400">Recording</span>
              </div>
            </div>

            {/* AI Avatar Status */}
            <div className="absolute bottom-4 left-4 z-20">
              <Badge className="bg-blue-primary/50 text-foreground backdrop-blur-sm">
                AI Avatar Active
              </Badge>
            </div>
          </div>

          {/* Video Controls */}
          <div className="bg-black/80 backdrop-blur-sm border-t border-border/20 p-4 flex items-center justify-center gap-3">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsMuted(!isMuted)}
              className={`p-3 rounded-lg transition-colors ${
                isMuted
                  ? 'bg-destructive/20 text-destructive'
                  : 'bg-muted hover:bg-muted/80 text-foreground'
              }`}
            >
              {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsCameraOff(!isCameraOff)}
              className={`p-3 rounded-lg transition-colors ${
                isCameraOff
                  ? 'bg-destructive/20 text-destructive'
                  : 'bg-muted hover:bg-muted/80 text-foreground'
              }`}
            >
              {isCameraOff ? <VideoOff className="w-5 h-5" /> : <Video className="w-5 h-5" />}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsScreenSharing(!isScreenSharing)}
              className={`p-3 rounded-lg transition-colors ${
                isScreenSharing
                  ? 'bg-accent/20 text-accent'
                  : 'bg-muted hover:bg-muted/80 text-foreground'
              }`}
            >
              <Share2 className="w-5 h-5" />
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="p-3 rounded-lg bg-destructive/20 hover:bg-destructive/30 text-destructive transition-colors ml-auto"
            >
              <Phone className="w-5 h-5" />
            </motion.button>
          </div>
        </motion.div>

        {/* Right Sidebar - Code Editor & Panels */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-2 flex flex-col gap-4 overflow-hidden"
        >
          {/* Code Editor Card */}
          <Card className="border border-border/40 flex-1 flex flex-col min-h-0">
            <CardHeader className="pb-3 flex-shrink-0">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Code2 className="w-4 h-4" />
                  Code Editor
                </CardTitle>
                <select
                  value={codeLanguage}
                  onChange={(e) => setCodeLanguage(e.target.value)}
                  className="px-2 py-1 rounded text-sm bg-muted border border-border/40 text-foreground"
                >
                  <option value="javascript">JavaScript</option>
                  <option value="python">Python</option>
                  <option value="typescript">TypeScript</option>
                </select>
              </div>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-hidden">
              <MonacoEditor
                height="100%"
                language={codeLanguage}
                value={code}
                onChange={(value) => setCode(value || '')}
                theme="vs-dark"
                options={{
                  minimap: { enabled: true },
                  fontSize: 12,
                  lineNumbers: 'on',
                  formatOnPaste: true,
                  formatOnType: true,
                }}
              />
            </CardContent>
          </Card>

          {/* Transcript/Chat Card */}
          <Card className="border border-border/40 flex-1 flex flex-col min-h-0">
            <CardHeader className="pb-3 flex-shrink-0">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  {activePanel === 'transcript' ? 'Live Transcript' : 'Interview Chat'}
                </CardTitle>
                <div className="flex gap-2">
                  <button
                    onClick={() => setActivePanel('transcript')}
                    className={`px-3 py-1 rounded text-sm transition-colors ${
                      activePanel === 'transcript'
                        ? 'bg-accent/10 text-accent'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Transcript
                  </button>
                  <button
                    onClick={() => setActivePanel('chat')}
                    className={`px-3 py-1 rounded text-sm transition-colors ${
                      activePanel === 'chat'
                        ? 'bg-accent/10 text-accent'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Chat
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-3 overflow-hidden p-3">
              {activePanel === 'transcript' && (
                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                  {transcript.map((entry, i) => (
                    <div key={i} className="text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-accent">{entry.speaker}</span>
                        <span className="text-xs text-muted-foreground">{entry.timestamp}</span>
                      </div>
                      <p className="text-foreground text-xs leading-relaxed">{entry.text}</p>
                    </div>
                  ))}
                </div>
              )}
              {activePanel === 'chat' && (
                <>
                  <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                    {messages.map((msg, i) => (
                      <div
                        key={i}
                        className={`text-sm p-2 rounded ${
                          msg.author === 'System'
                            ? 'bg-muted text-muted-foreground text-center'
                            : 'bg-accent/10 text-foreground'
                        }`}
                      >
                        <span className="font-semibold text-xs">{msg.author}</span>
                        <p className="text-xs mt-1">{msg.text}</p>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2 flex-shrink-0 pt-2 border-t border-border/40">
                    <input
                      type="text"
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                      placeholder="Message..."
                      className="flex-1 px-2 py-1 rounded text-sm bg-muted border border-border/40 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent"
                    />
                    <button
                      onClick={sendMessage}
                      className="p-1 rounded bg-accent hover:bg-accent/90 text-accent-foreground transition-colors"
                    >
                      <MessageCircle className="w-4 h-4" />
                    </button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
