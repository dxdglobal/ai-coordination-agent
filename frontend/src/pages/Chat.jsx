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
  SmartToy,
  Person,
  AutoAwesome,
  Psychology,
  Assignment,
  Folder,
  Lightbulb,
  Mic,
  AttachFile,
  Storage,
  Analytics,
  BarChart,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'

const Chat = () => {
  const { aiAPI, loading, error, setError } = useAPI()
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const predefinedPrompts = [
    {
      label: 'Database Stats',
      prompt: 'How many tables are in the database?',
      icon: <Storage />,
      type: 'database'
    },
    {
      label: 'Total Projects',
      prompt: 'How many total projects do we have?',
      icon: <Folder />,
      type: 'database'
    },
    {
      label: 'Total Tasks',
      prompt: 'Show me total tasks and their breakdown by status',
      icon: <Assignment />,
      type: 'database'
    },
    {
      label: 'Analytics Overview',
      prompt: 'Give me a complete analytics overview of all data',
      icon: <Analytics />,
      type: 'database'
    },
    {
      label: 'Task Completion',
      prompt: 'What is the task completion rate?',
      icon: <BarChart />,
      type: 'database'
    },
    {
      label: 'Search Projects',
      prompt: 'Search for projects and tasks',
      icon: <Psychology />,
      type: 'search'
    },
    {
      label: 'Recent Activity',
      prompt: 'Show me recent activity and latest updates',
      icon: <Lightbulb />,
      type: 'database'
    },
    {
      label: 'AI Providers',
      prompt: 'Show me available AI providers and their status',
      icon: <AutoAwesome />,
      type: 'providers'
    }
  ]

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Focus on input when component mounts
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    setShowWelcome(false)
    
    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date(),
      type: 'message'
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsAnalyzing(true)

    try {
      // Use the new smart chat endpoint that automatically routes queries
      const response = await fetch('http://localhost:5000/ai/smart-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: inputMessage })
      })
      
      if (!response.ok) {
        throw new Error('Failed to get AI response')
      }
      
      const result = await response.json()
      
      const aiMessage = {
        id: Date.now() + 1,
        text: result.response,
        sender: 'ai',
        timestamp: new Date(),
        type: result.type,
        data: result.data,
        intent_analysis: result.intent_analysis,
        provider_used: result.provider_used
      }
      
      setMessages(prev => [...prev, aiMessage])
    } catch (err) {
      console.error('Error:', err)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your request. Please try again.',
        sender: 'ai',
        timestamp: new Date(),
        type: 'error'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handlePredefinedPrompt = async (prompt) => {
    setShowWelcome(false)
    setIsAnalyzing(true)
    
    const userMessage = {
      id: Date.now(),
      text: prompt.prompt,
      sender: 'user',
      timestamp: new Date(),
      type: 'prompt'
    }

    setMessages(prev => [...prev, userMessage])

    try {
      if (prompt.type === 'providers') {
        // Special handling for AI providers query
        const response = await fetch('http://localhost:5000/ai/providers', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        })
        
        if (!response.ok) {
          throw new Error('Failed to get AI providers')
        }
        
        const result = await response.json()
        
        let providersText = `Available AI Providers:\n\n`
        result.providers.forEach(provider => {
          providersText += `🤖 ${provider.credential_name}\n`
          providersText += `   Type: ${provider.credential_type}\n`
          providersText += `   Model: ${provider.model}\n`
          providersText += `   Status: ${provider.status}\n`
          providersText += `   Environment: ${provider.environment}\n\n`
        })
        providersText += `Default Provider: ${result.default_provider}`
        
        const aiMessage = {
          id: Date.now() + 1,
          text: providersText,
          sender: 'ai',
          timestamp: new Date(),
          type: 'providers-info',
          data: result
        }
        
        setMessages(prev => [...prev, aiMessage])
      } else {
        // Use smart chat for all other prompts
        const response = await fetch('http://localhost:5000/ai/smart-chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: prompt.prompt })
        })
        
        if (!response.ok) {
          throw new Error('Failed to get AI response')
        }
        
        const result = await response.json()
        
        const aiMessage = {
          id: Date.now() + 1,
          text: result.response,
          sender: 'ai',
          timestamp: new Date(),
          type: result.type,
          data: result.data,
          intent_analysis: result.intent_analysis,
          provider_used: result.provider_used
        }
        
        setMessages(prev => [...prev, aiMessage])
      }
    } catch (err) {
      console.error('Error:', err)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your request. Please try again.',
        sender: 'ai',
        timestamp: new Date(),
        type: 'error'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsAnalyzing(false)
    }
  }

  const formatAnalysisResponse = (analysis) => {
    if (typeof analysis === 'string') return analysis
    
    if (analysis.raw_analysis) return analysis.raw_analysis
    
    let formatted = "Workspace Analysis Results\n\n"
    
    if (analysis.status_overview) {
      formatted += "Current Status Overview\n"
      formatted += `${analysis.status_overview}\n\n`
    }
    
    if (analysis.issues) {
      formatted += "Issues Requiring Attention\n"
      if (Array.isArray(analysis.issues)) {
        analysis.issues.forEach(issue => formatted += `• ${issue}\n`)
      } else {
        formatted += `${analysis.issues}\n`
      }
      formatted += "\n"
    }
    
    if (analysis.recommendations) {
      formatted += "Recommended Actions\n"
      if (Array.isArray(analysis.recommendations)) {
        analysis.recommendations.forEach(rec => formatted += `• ${rec}\n`)
      } else {
        formatted += `${analysis.recommendations}\n`
      }
      formatted += "\n"
    }
    
    return formatted
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const renderMessage = (message) => {
    const isUser = message.sender === 'user'
    const isAI = message.sender === 'ai'

    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 2,
          mb: 3,
          maxWidth: '678px',
          mx: 'auto',
          px: 2,
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            backgroundColor: isAI ? '#333333' : '#555555',
          }}
        >
          {isAI ? <SmartToy sx={{ fontSize: 18 }} /> : <Person sx={{ fontSize: 18 }} />}
        </Avatar>
        
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#ffffff' }}>
              {isAI ? 'AI Agent' : 'You'}
            </Typography>
            {message.provider_used && (
              <Chip 
                label={message.provider_used} 
                size="small" 
                variant="outlined"
                sx={{ 
                  height: 20, 
                  fontSize: '0.7rem',
                  color: '#888888', 
                  borderColor: '#444444' 
                }}
              />
            )}
            <Typography variant="caption" sx={{ color: '#888888' }}>
              {formatTimestamp(message.timestamp)}
            </Typography>
          </Box>
          
          <Typography
            sx={{
              color: '#ffffff',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              lineHeight: 1.6,
            }}
          >
            {message.text}
          </Typography>
          
          {/* Display database analytics data if available */}
          {message.type === 'database-analytics' && message.data && (
            <Box sx={{ mt: 2 }}>
              <Paper 
                sx={{ 
                  p: 2, 
                  backgroundColor: '#1a1a1a', 
                  border: '1px solid #333333',
                  maxWidth: '100%',
                  overflow: 'auto'
                }}
              >
                <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                  📊 Database Statistics
                </Typography>
                
                {message.data.application_tables && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: '#bbbbbb', mb: 1 }}>
                      📋 Application Data:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      <Chip 
                        label={`Projects: ${message.data.application_tables.projects}`} 
                        variant="outlined" 
                        size="small"
                        sx={{ color: '#ffffff', borderColor: '#555555' }}
                      />
                      <Chip 
                        label={`Tasks: ${message.data.application_tables.tasks}`} 
                        variant="outlined" 
                        size="small"
                        sx={{ color: '#ffffff', borderColor: '#555555' }}
                      />
                      <Chip 
                        label={`Comments: ${message.data.application_tables.comments}`} 
                        variant="outlined" 
                        size="small"
                        sx={{ color: '#ffffff', borderColor: '#555555' }}
                      />
                      <Chip 
                        label={`Labels: ${message.data.application_tables.labels}`} 
                        variant="outlined" 
                        size="small"
                        sx={{ color: '#ffffff', borderColor: '#555555' }}
                      />
                      <Chip 
                        label={`Integrations: ${message.data.application_tables.integrations}`} 
                        variant="outlined" 
                        size="small"
                        sx={{ color: '#ffffff', borderColor: '#555555' }}
                      />
                    </Box>
                  </Box>
                )}
                
                {message.data.task_analysis && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: '#bbbbbb', mb: 1 }}>
                      ✅ Task Analysis:
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#cccccc', mb: 1 }}>
                      Completion Rate: {message.data.task_analysis.completion_rate?.toFixed(1)}%
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {Object.entries(message.data.task_analysis.by_status || {}).map(([status, count]) => (
                        <Chip 
                          key={status}
                          label={`${status.replace('_', ' ')}: ${count}`} 
                          variant="outlined" 
                          size="small"
                          sx={{ color: '#ffffff', borderColor: '#555555' }}
                        />
                      ))}
                    </Box>
                  </Box>
                )}
                
                {message.data.total_tables && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ color: '#bbbbbb', mb: 1 }}>
                      🗄️ Database Info:
                    </Typography>
                    <Chip 
                      label={`Total Tables: ${message.data.total_tables}`} 
                      variant="outlined" 
                      size="small"
                      sx={{ color: '#ffffff', borderColor: '#555555' }}
                    />
                  </Box>
                )}
              </Paper>
            </Box>
          )}
        </Box>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#0f0f0f',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          position: 'absolute',
          top: 24,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 10,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ backgroundColor: '#333333' }}>
            <SmartToy />
          </Avatar>
          <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600 }}>
            AI Coordination Agent
          </Typography>
        </Box>
      </Box>

      {/* Main Content Area */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: showWelcome ? 'center' : 'flex-start',
          alignItems: 'center',
          px: 1,
          pt: showWelcome ? 0 : 12,
          pb: 3,
        }}
      >
        {/* Welcome Screen */}
        {showWelcome && (
          <Box
            sx={{
              textAlign: 'center',
              maxWidth: '678px',
              mx: 'auto',
              mb: 6,
              px: 2,
            }}
          >
            <Typography
              variant="h3"
              sx={{
                color: '#ffffff',
                fontWeight: 600,
                mb: 3,
                fontSize: { xs: '2rem', md: '3rem' },
              }}
            >
              Hey! What's up? Ready to dive into whatever you're curious about today?
            </Typography>
            
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 1,
                justifyContent: 'center',
                mb: 4,
              }}
            >
              {predefinedPrompts.map((prompt, index) => (
                <Chip
                  key={index}
                  label={prompt.label}
                  onClick={() => handlePredefinedPrompt(prompt)}
                  sx={{
                    backgroundColor: '#1a1a1a',
                    color: '#ffffff',
                    border: '1px solid #333333',
                    '&:hover': {
                      backgroundColor: '#2a2a2a',
                      border: '1px solid #555555',
                    },
                    cursor: 'pointer',
                  }}
                  icon={React.cloneElement(prompt.icon, { sx: { color: '#ffffff' } })}
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Messages */}
        {!showWelcome && (
          <Box
            sx={{
              flex: 1,
              overflow: 'auto',
              maxWidth: '678px',
              width: '100%',
              mx: 'auto',
              mb: 3,
            }}
          >
            {messages.map(renderMessage)}
            
            {isAnalyzing && (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 2,
                  mb: 3,
                  maxWidth: '678px',
                  mx: 'auto',
                  px: 2,
                }}
              >
                <Avatar sx={{ width: 32, height: 32, backgroundColor: '#333333' }}>
                  <SmartToy sx={{ fontSize: 18 }} />
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: '#ffffff', mb: 1 }}>
                    AI Agent
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        display: 'flex',
                        gap: 0.5,
                      }}
                    >
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#666666',
                          animation: 'pulse 1.4s ease-in-out infinite',
                          animationDelay: '0s',
                        }}
                      />
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#666666',
                          animation: 'pulse 1.4s ease-in-out infinite',
                          animationDelay: '0.2s',
                        }}
                      />
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: '#666666',
                          animation: 'pulse 1.4s ease-in-out infinite',
                          animationDelay: '0.4s',
                        }}
                      />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#888888' }}>
                      Thinking...
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}
            
            <div ref={messagesEndRef} />
          </Box>
        )}

        {/* Input Area */}
        <Box
          sx={{
            maxWidth: '678px',
            width: '100%',
            mx: 'auto',
            position: 'relative',
            px: 2,
          }}
        >
          <TextField
            ref={inputRef}
            fullWidth
            variant="outlined"
            placeholder="How can AI Coordination Agent help?"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            multiline
            maxRows={6}
            disabled={isAnalyzing}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="Voice input">
                      <IconButton
                        size="small"
                        sx={{ color: '#888888', '&:hover': { color: '#ffffff' } }}
                      >
                        <Mic />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Attach file">
                      <IconButton
                        size="small"
                        sx={{ color: '#888888', '&:hover': { color: '#ffffff' } }}
                      >
                        <AttachFile />
                      </IconButton>
                    </Tooltip>
                    <IconButton
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || isAnalyzing}
                      sx={{
                        color: inputMessage.trim() && !isAnalyzing ? '#ffffff' : '#666666',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        },
                      }}
                    >
                      <Send />
                    </IconButton>
                  </Box>
                </InputAdornment>
              ),
              sx: {
                backgroundColor: '#1a1a1a',
                borderRadius: '24px',
                '& fieldset': {
                  border: '1px solid #333333',
                },
                '&:hover fieldset': {
                  border: '1px solid #555555',
                },
                '&.Mui-focused fieldset': {
                  border: '1px solid #777777',
                },
                '& .MuiInputBase-input': {
                  color: '#ffffff',
                  '&::placeholder': {
                    color: '#888888',
                    opacity: 1,
                  },
                },
              },
            }}
          />
        </Box>
      </Box>

      {/* CSS for animations */}
      <style>
        {`
          @keyframes pulse {
            0%, 80%, 100% {
              opacity: 0.3;
              transform: scale(0.8);
            }
            40% {
              opacity: 1;
              transform: scale(1);
            }
          }
        `}
      </style>
    </Box>
  )
}

export default Chat