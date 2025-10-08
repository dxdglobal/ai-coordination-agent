import React, { useState, useEffect, useRef } from 'react'
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Paper,
  Tabs,
  Tab,
  TextField,
  IconButton,
  Avatar,
  InputAdornment,
  CircularProgress,
} from '@mui/material'
import {
  FolderOpen,
  Send,
  SmartToy,
  Chat,
  ViewList,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'

const Projects = () => {
  const { projectAPI, loading, error, setError } = useAPI()
  const [projects, setProjects] = useState([])
  const [currentTab, setCurrentTab] = useState(0)
  
  // Chat system state
  const [chatMessages, setChatMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const chatEndRef = useRef(null)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const data = await projectAPI.getAll()
      setProjects(data)
    } catch (err) {
      console.error('Failed to load projects:', err)
      // Error is already set by projectAPI.getAll()
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'done': return 'success'
      case 'in_progress': return 'primary'
      case 'review': return 'warning'
      case 'blocked': return 'error'
      default: return 'default'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString()
  }

  // Chat system functions
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatMessages])

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || isChatLoading) return

    const userMessage = {
      id: Date.now(),
      text: currentMessage,
      isUser: true,
      timestamp: new Date()
    }

    setChatMessages(prev => [...prev, userMessage])
    setCurrentMessage('')
    setIsChatLoading(true)

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentMessage,
          context: {
            projects: projects,
            currentPage: 'projects'
          }
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const aiMessage = {
          id: Date.now() + 1,
          text: data.response,
          isUser: false,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, aiMessage])
      } else {
        throw new Error('Failed to get AI response')
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date(),
        isError: true
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <Container maxWidth="lg" style={{ marginTop: '40px' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3}} >
        <Typography variant="h4">Projects</Typography>
        <Typography variant="body2" color="text.secondary">
          View project information and status
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={currentTab} 
          onChange={(e, newValue) => setCurrentTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab 
            icon={<ViewList />} 
            label="Project List" 
            iconPosition="start"
          />
          <Tab 
            icon={<SmartToy />} 
            label="AI Coordinator" 
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {currentTab === 0 && (
        <>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <LinearProgress sx={{ width: '100%', maxWidth: 400 }} />
            </Box>
          ) : projects.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <FolderOpen sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No projects found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Projects will appear here when they are available
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={3} style={{ mt: 40 }}>
              {projects.map((project) => (
                <Grid item xs={12} sm={6} md={4} key={project.id}>
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Typography gutterBottom variant="h6" component="div">
                        {project.name}
                      </Typography>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {project.description || 'No description'}
                      </Typography>

                      <Box sx={{ mb: 2 }}>
                        <Chip
                          label={project.status?.replace('_', ' ')}
                          color={getStatusColor(project.status)}
                          size="small"
                        />
                      </Box>

                      <Typography variant="body2" color="text.secondary">
                        Tasks: {project.task_count || 0}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">
                        Deadline: {formatDate(project.deadline)}
                      </Typography>
                    </CardContent>

                    <CardActions>
                      <Button
                        size="small"
                        startIcon={<FolderOpen />}
                        onClick={() => window.location.href = `/tasks?project_id=${project.id}`}
                      >
                        View Tasks
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </>
      )}

      {currentTab === 1 && (
        <Box sx={{ minHeight: '600px' }}>
          {/* AI Coordinator Chat */}
          <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ borderBottom: 1, borderColor: 'divider', pb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SmartToy />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    AI Coordinator
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ask me anything about your projects and their status
                  </Typography>
                </Box>
              </Box>
            </CardContent>
            
            {/* Chat Messages */}
            <CardContent sx={{ 
              flex: 1, 
              overflow: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              maxHeight: '400px'
            }}>
              {chatMessages.length === 0 ? (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  height: '100%',
                  color: 'text.secondary'
                }}>
                  <Chat sx={{ fontSize: 64, mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Start a conversation
                  </Typography>
                  <Typography variant="body2" textAlign="center">
                    Ask me about your projects, their status, deadlines, or anything else you need help with.
                  </Typography>
                </Box>
              ) : (
                chatMessages.map((message) => (
                  <Box
                    key={message.id}
                    sx={{
                      display: 'flex',
                      justifyContent: message.isUser ? 'flex-end' : 'flex-start',
                      mb: 1
                    }}
                  >
                    <Box
                      sx={{
                        maxWidth: '70%',
                        padding: 2,
                        borderRadius: 2,
                        backgroundColor: message.isUser 
                          ? 'primary.main' 
                          : message.isError 
                            ? 'error.light'
                            : 'grey.100',
                        color: message.isUser ? 'white' : 'text.primary'
                      }}
                    >
                      <Typography variant="body1">
                        {message.text}
                      </Typography>
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          opacity: 0.7,
                          display: 'block',
                          mt: 0.5
                        }}
                      >
                        {message.timestamp.toLocaleTimeString()}
                      </Typography>
                    </Box>
                  </Box>
                ))
              )}
              <div ref={chatEndRef} />
            </CardContent>
            
            {/* Chat Input */}
            <CardContent sx={{ borderTop: 1, borderColor: 'divider', pt: 2 }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me about your projects..."
                  variant="outlined"
                  size="small"
                  disabled={isChatLoading}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        {isChatLoading && <CircularProgress size={20} />}
                      </InputAdornment>
                    )
                  }}
                />
                <IconButton
                  color="primary"
                  onClick={handleSendMessage}
                  disabled={!currentMessage.trim() || isChatLoading}
                  sx={{ alignSelf: 'flex-end' }}
                >
                  <Send />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}
    </Container>
  )
}

export default Projects