import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  TextField,
  Typography,
  IconButton,
  Chip,
  Avatar,
  InputAdornment,
  Tooltip,
  Paper,
  CircularProgress,
  Divider,
} from '@mui/material'
import {
  Send,
  Lightbulb,
  Psychology,
  Storage,
  BarChart,
  Assignment,
  Folder,
  Analytics,
  Mic,
  MicOff,
  Language,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'

export default function Chat() {
  const { apiUrl } = useAPI()
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const predefinedPrompts = [
    {
      label: 'Hamza Projects',
      prompt: 'Show me all of Hamza\'s current projects',
      icon: <Folder />,
      type: 'database'
    },
    {
      label: 'Hamza Tasks',
      prompt: 'Give me details of Hamza project tasks',
      icon: <Assignment />,
      type: 'database'
    },
    {
      label: 'Overdue Tasks',
      prompt: 'Show me Hamza\'s overdue tasks',
      icon: <Analytics />,
      type: 'database'
    },
    {
      label: 'In Progress',
      prompt: 'What tasks is Hamza currently working on?',
      icon: <BarChart />,
      type: 'database'
    },
    {
      label: 'Completed Tasks',
      prompt: 'Show me Hamza\'s completed tasks',
      icon: <Storage />,
      type: 'database'
    },
    {
      label: 'Project Status',
      prompt: 'What is the status of Hamza\'s projects?',
      icon: <Psychology />,
      type: 'database'
    }
  ]

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return

    const currentMessage = messageText.trim()
    setInputMessage('')
    setIsAnalyzing(true)
    setShowWelcome(false)

    // Add user message
    const userMessage = {
      id: Date.now(),
      text: currentMessage,
      sender: 'user',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])

    try {
      // Call the real database server
      const response = await fetch('http://localhost:5001/api/smart-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: currentMessage })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const result = await response.json()
      
      const aiMessage = {
        id: Date.now() + 1,
        text: result.response,
        sender: 'ai',
        timestamp: new Date(),
        type: result.type || 'message',
        data: result.data || null,
        source: 'real_database'
      }

      setMessages(prev => [...prev, aiMessage])
      
    } catch (error) {
      console.error('Error calling real database API:', error)
      
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error while connecting to the database. Please ensure the real database server is running on port 5001.',
        sender: 'ai',
        timestamp: new Date(),
        type: 'error'
      }
      setMessages(prev => [...prev, errorMessage])
    }

    setIsAnalyzing(false)
  }

  const handleSendMessage = async () => {
    await sendMessage(inputMessage)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handlePredefinedPrompt = async (prompt) => {
    await sendMessage(prompt)
  }

  const formatMessage = (message) => {
    if (!message.text) return ''

    // Handle markdown-style formatting
    let formatted = message.text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>')

    return { __html: formatted }
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#f5f5f5' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, bgcolor: '#1976d2', color: 'white' }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', textAlign: 'center' }}>
          🤖 AI Coordination Agent - Real Database
        </Typography>
        <Typography variant="body2" sx={{ textAlign: 'center', opacity: 0.9 }}>
          Connected to Real CRM Database | Hamza Projects & Tasks
        </Typography>
      </Paper>

      {/* Messages Container */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {showWelcome && (
          <Paper elevation={2} sx={{ p: 3, mb: 3, bgcolor: '#e3f2fd', borderRadius: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, color: '#1565c0', fontWeight: 'bold' }}>
              🚀 Welcome to Real Database Integration!
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              I'm now connected to the actual CRM database with <strong>real data</strong>. 
              All mock data has been removed. Ask me about:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {predefinedPrompts.map((prompt, index) => (
                <Chip
                  key={index}
                  label={prompt.label}
                  icon={prompt.icon}
                  onClick={() => handlePredefinedPrompt(prompt.prompt)}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': { bgcolor: '#1976d2', color: 'white' }
                  }}
                />
              ))}
            </Box>
            <Typography variant="body2" sx={{ fontStyle: 'italic', color: '#666' }}>
              💡 Click any chip above or type your question about Hamza's projects and tasks!
            </Typography>
          </Paper>
        )}

        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
              mb: 2,
            }}
          >
            <Paper
              elevation={2}
              sx={{
                p: 2,
                maxWidth: '70%',
                bgcolor: message.sender === 'user' ? '#1976d2' : '#fff',
                color: message.sender === 'user' ? 'white' : 'black',
                borderRadius: 2,
                position: 'relative',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: message.sender === 'user' ? '#1565c0' : '#4caf50',
                    fontSize: '0.875rem',
                  }}
                >
                  {message.sender === 'user' ? '👤' : '🤖'}
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography
                    variant="body1"
                    dangerouslySetInnerHTML={formatMessage(message)}
                  />
                  {message.source === 'real_database' && (
                    <Chip
                      label="Real Database"
                      size="small"
                      sx={{ 
                        mt: 1, 
                        bgcolor: '#4caf50', 
                        color: 'white',
                        fontSize: '0.7rem'
                      }}
                    />
                  )}
                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      mt: 1,
                      opacity: 0.7,
                      fontSize: '0.75rem',
                    }}
                  >
                    {message.timestamp?.toLocaleTimeString()}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Box>
        ))}

        {isAnalyzing && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Paper elevation={2} sx={{ p: 2, bgcolor: '#fff', borderRadius: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ width: 32, height: 32, bgcolor: '#4caf50' }}>
                  🤖
                </Avatar>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2">
                    Querying real database...
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper elevation={3} sx={{ p: 2, bgcolor: 'white' }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask me about Hamza's projects, tasks, status, or deadlines..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isAnalyzing}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <Tooltip title="Send Message">
                    <IconButton
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || isAnalyzing}
                      sx={{ color: '#1976d2' }}
                    >
                      <Send />
                    </IconButton>
                  </Tooltip>
                </InputAdornment>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              },
            }}
          />
        </Box>

        <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center' }}>
          <Typography variant="caption" sx={{ color: '#666' }}>
            🔄 Real Database Mode | Port 5001 | No Mock Data
          </Typography>
        </Box>
      </Paper>
    </Box>
  )
}