import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  CircularProgress,
  Fade,
  Divider,
  Card,
  CardContent,
  Button,
  Tooltip,
} from '@mui/material'
import {
  Send,
  Psychology,
  Person,
  SmartToy,
  AutoAwesome,
  TrendingUp,
  Assignment,
  People,
  Clear,
  ContentCopy,
  ThumbUp,
  ThumbDown,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'

const AICoordinatorChat = () => {
  const { aiAPI } = useAPI()
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: "Hello! I'm your AI Coordinator. I can help you with employee performance analysis, task management, project insights, and much more. What would you like to know?",
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [suggestions] = useState([
    "Give me Hamza's performance report",
    "Show me overdue tasks",
    "What's the project status?",
    "Analyze team productivity",
    "Create a new task",
  ])
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Check if it's an employee query
      if (input.toLowerCase().includes('performance') || 
          input.toLowerCase().includes('report') || 
          input.toLowerCase().includes('task') ||
          /\b(hamza|john|sarah|mike|alex|lisa)\b/i.test(input)) {
        
        const response = await fetch('http://127.0.0.1:5001/ai/employee-analysis', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: input.trim() }),
        })

        const data = await response.json()
        
        if (data.success) {
          const assistantMessage = {
            id: Date.now() + 1,
            type: 'assistant',
            content: data.analysis,
            timestamp: new Date(),
            metadata: {
              employee: data.employee,
              queryAnalysis: data.query_analysis,
              performanceData: data.performance_data,
            }
          }
          setMessages(prev => [...prev, assistantMessage])
        } else {
          throw new Error(data.error || 'Employee analysis failed')
        }
      } else {
        // Regular chat
        const response = await fetch('http://127.0.0.1:5001/ai/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            message: input.trim(),
            context: 'ai_coordinator' 
          }),
        })

        const data = await response.json()
        
        if (data.success) {
          const assistantMessage = {
            id: Date.now() + 1,
            type: 'assistant',
            content: data.response,
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, assistantMessage])
        } else {
          throw new Error(data.error || 'Chat failed')
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `I apologize, but I encountered an error: ${error.message}. Please try again or rephrase your question.`,
        timestamp: new Date(),
        isError: true,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion)
    inputRef.current?.focus()
  }

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        type: 'assistant',
        content: "Hello! I'm your AI Coordinator. I can help you with employee performance analysis, task management, project insights, and much more. What would you like to know?",
        timestamp: new Date(),
      }
    ])
  }

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content)
  }

  const renderMessage = (message) => {
    const isUser = message.type === 'user'
    const isError = message.isError

    return (
      <Fade in={true} key={message.id}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            mb: 2,
            alignItems: 'flex-start',
          }}
        >
          {!isUser && (
            <Avatar
              sx={{
                bgcolor: isError ? 'error.main' : 'primary.main',
                mr: 2,
                mt: 0.5,
              }}
            >
              <Psychology />
            </Avatar>
          )}
          
          <Box sx={{ maxWidth: '70%', minWidth: '200px' }}>
            <Paper
              elevation={1}
              sx={{
                p: 2,
                bgcolor: isUser ? 'primary.main' : isError ? 'error.dark' : 'background.paper',
                color: isUser ? 'primary.contrastText' : 'text.primary',
                borderRadius: 2,
                position: 'relative',
              }}
            >
              <Typography
                variant="body1"
                sx={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  lineHeight: 1.6,
                }}
              >
                {message.content}
              </Typography>

              {/* Performance Data Card */}
              {message.metadata?.performanceData && (
                <Card sx={{ mt: 2, bgcolor: 'background.default' }}>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom color="primary">
                      📊 Performance Summary - {message.metadata.employee}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      <Chip 
                        label={`Total: ${message.metadata.performanceData.total_tasks}`}
                        color="default"
                        size="small"
                      />
                      <Chip 
                        label={`Completed: ${message.metadata.performanceData.completed_tasks}`}
                        color="success"
                        size="small"
                      />
                      <Chip 
                        label={`In Progress: ${message.metadata.performanceData.in_progress_tasks}`}
                        color="info"
                        size="small"
                      />
                      <Chip 
                        label={`Overdue: ${message.metadata.performanceData.overdue_tasks}`}
                        color="error"
                        size="small"
                      />
                      <Chip 
                        label={`${message.metadata.performanceData.completion_rate}% Complete`}
                        color="primary"
                        size="small"
                      />
                    </Box>
                    
                    {message.metadata.queryAnalysis && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          🤖 AI Analysis: {message.metadata.queryAnalysis.intent} 
                          (Confidence: {(message.metadata.queryAnalysis.confidence * 100).toFixed(0)}%)
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              )}

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                <Typography
                  variant="caption"
                  sx={{
                    color: isUser ? 'primary.contrastText' : 'text.secondary',
                    opacity: 0.7,
                  }}
                >
                  {message.timestamp.toLocaleTimeString()}
                </Typography>
                
                {!isUser && (
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="Copy message">
                      <IconButton
                        size="small"
                        onClick={() => copyMessage(message.content)}
                        sx={{ color: 'text.secondary' }}
                      >
                        <ContentCopy fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Good response">
                      <IconButton size="small" sx={{ color: 'text.secondary' }}>
                        <ThumbUp fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Poor response">
                      <IconButton size="small" sx={{ color: 'text.secondary' }}>
                        <ThumbDown fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                )}
              </Box>
            </Paper>
          </Box>

          {isUser && (
            <Avatar
              sx={{
                bgcolor: 'secondary.main',
                ml: 2,
                mt: 0.5,
              }}
            >
              <Person />
            </Avatar>
          )}
        </Box>
      </Fade>
    )
  }

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      {/* Header */}
      <Paper
        elevation={1}
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          bgcolor: 'background.paper',
          borderRadius: 0,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <SmartToy />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              AI Coordinator
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Powered by OpenAI GPT-3.5 Turbo
            </Typography>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            icon={<AutoAwesome />}
            label="Smart Analysis"
            color="primary"
            variant="outlined"
            size="small"
          />
          <Button
            startIcon={<Clear />}
            onClick={clearChat}
            size="small"
            variant="outlined"
          >
            Clear Chat
          </Button>
        </Box>
      </Paper>

      {/* Suggestions */}
      {messages.length === 1 && (
        <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            💡 Try asking:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {suggestions.map((suggestion, index) => (
              <Chip
                key={index}
                label={suggestion}
                onClick={() => handleSuggestionClick(suggestion)}
                sx={{ cursor: 'pointer' }}
                variant="outlined"
                size="small"
              />
            ))}
          </Box>
        </Box>
      )}

      <Divider />

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            bgcolor: 'background.default',
          },
          '&::-webkit-scrollbar-thumb': {
            bgcolor: 'primary.main',
            borderRadius: '4px',
          },
        }}
      >
        {messages.map(renderMessage)}
        
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
              <Psychology />
            </Avatar>
            <Paper
              elevation={1}
              sx={{
                p: 2,
                bgcolor: 'background.paper',
                borderRadius: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 2,
              }}
            >
              <CircularProgress size={20} />
              <Typography color="text.secondary">
                AI Coordinator is thinking...
              </Typography>
            </Paper>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Paper
        elevation={8}
        sx={{
          p: 2,
          bgcolor: 'background.paper',
          borderRadius: 0,
        }}
      >
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about tasks, employees, projects, or performance..."
            variant="outlined"
            disabled={isLoading}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                bgcolor: 'background.default',
              },
            }}
          />
          <IconButton
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'action.disabledBackground',
              },
            }}
          >
            <Send />
          </IconButton>
        </Box>
        
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mt: 1, textAlign: 'center' }}
        >
          AI Coordinator can analyze employee performance, manage tasks, and provide intelligent insights.
        </Typography>
      </Paper>
    </Box>
  )
}

export default AICoordinatorChat