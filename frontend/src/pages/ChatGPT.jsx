import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  Typography,
  IconButton,
  Chip,
  Avatar,
  Fade,
  Fab,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Send,
  SmartToy,
  Person,
  Folder,
  Assignment,
  Analytics,
  BarChart,
  Storage,
  Psychology,
  LightbulbOutlined,
  Menu as MenuIcon,
  Dashboard,
  IntegrationInstructions,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import './ChatGPT.css'

const ChatGPT = () => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const [menuAnchor, setMenuAnchor] = useState(null)
  const [sessionId, setSessionId] = useState(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`) // Generate unique session ID
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  const navigationItems = [
    { title: 'Classic Chat', path: '/chat-real', icon: <SmartToy /> },
    { title: 'RL Chat', path: '/rl-chat', icon: <Psychology /> },
    { title: 'Dashboard', path: '/dashboard', icon: <Dashboard /> },
    { title: 'Projects', path: '/projects', icon: <Folder /> },
    { title: 'Tasks', path: '/tasks', icon: <Assignment /> },
    { title: 'Integrations', path: '/integrations', icon: <IntegrationInstructions /> },
  ]

  const predefinedPrompts = [
    {
      label: 'Employee List',
      prompt: 'Show me employee list',
      icon: <Folder />,
    },
    {
      label: 'All Projects',
      prompt: 'About projects',
      icon: <Assignment />,
    },
    {
      label: 'Overdue Projects',
      prompt: 'Show me overdue projects',
      icon: <Analytics />,
    },
    {
      label: 'Project Tasks',
      prompt: 'Show me project tasks',
      icon: <BarChart />,
    },
    {
      label: 'Employee Performance',
      prompt: 'Show me performance analysis',
      icon: <Storage />,
    },
    {
      label: 'Project Status',
      prompt: 'What is the overall project status?',
      icon: <Psychology />,
    }
  ]

  const handleMenuClick = (event) => {
    setMenuAnchor(event.currentTarget)
  }

  const handleMenuClose = () => {
    setMenuAnchor(null)
  }

  const handleNavigation = (path) => {
    navigate(path)
    handleMenuClose()
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputMessage.trim() || isAnalyzing) return

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setShowWelcome(false)
    setIsAnalyzing(true)

    try {
      const response = await fetch('http://localhost:5001/ai/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: inputMessage,
          session_id: sessionId  // Include session ID for conversation history
        })
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const result = await response.json()

      const aiMessage = {
        id: Date.now() + 1,
        text: result.response || 'Sorry, I could not process your request.',
        sender: 'ai',
        timestamp: new Date(),
        data: result.employee_data || result.project_data || result.data
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please make sure the backend server is running and try again.',
        sender: 'ai',
        timestamp: new Date(),
        error: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleQuickAction = (prompt) => {
    setInputMessage(prompt)
    inputRef.current?.focus()
  }

  const renderMessage = (message) => {
    if (message.sender === 'user') {
      return (
        <Fade in={true} key={message.id}>
          <div className="message-container">
            <div className="message-bubble user-message">
              <Typography variant="body1" sx={{ fontSize: '15px', fontWeight: 400 }}>
                {message.text}
              </Typography>
            </div>
          </div>
        </Fade>
      )
    } else {
      return (
        <Fade in={true} key={message.id}>
          <div className="message-container">
            <div className="ai-message-container">
              <Avatar className="message-avatar" sx={{ bgcolor: '#10a37f' }}>
                <SmartToy sx={{ fontSize: 18 }} />
              </Avatar>
              <div className="message-bubble ai-message">
                <Typography 
                  variant="body1" 
                  sx={{ 
                    fontSize: '15px', 
                    fontWeight: 400,
                    whiteSpace: 'pre-line',
                    color: message.error ? '#e53e3e' : '#e1e5e9'
                  }}
                >
                  {message.text}
                </Typography>
              </div>
            </div>
          </div>
        </Fade>
      )
    }
  }

  const renderTypingIndicator = () => (
    <div className="message-container">
      <div className="ai-message-container">
        <Avatar className="message-avatar" sx={{ bgcolor: '#10a37f' }}>
          <SmartToy sx={{ fontSize: 18 }} />
        </Avatar>
        <div className="typing-indicator">
          <div className="loading-dots">
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="chatgpt-container">
      {/* Floating Navigation Menu */}
      <Fab
        color="primary"
        aria-label="menu"
        onClick={handleMenuClick}
        sx={{
          position: 'fixed',
          top: 20,
          right: 20,
          zIndex: 1000,
          background: 'linear-gradient(135deg, #10a37f 0%, #08d17a 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #0d8b6b 0%, #06b86a 100%)',
            transform: 'scale(1.05)',
          },
          transition: 'all 0.3s ease',
        }}
      >
        <MenuIcon />
      </Fab>

      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            mt: 1,
            background: 'rgba(40, 40, 40, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '12px',
            color: '#e1e5e9',
          },
        }}
      >
        {navigationItems.map((item, index) => (
          <MenuItem 
            key={index} 
            onClick={() => handleNavigation(item.path)}
            sx={{ 
              color: '#e1e5e9',
              '&:hover': {
                background: 'rgba(16, 163, 127, 0.1)',
              }
            }}
          >
            <ListItemIcon sx={{ color: '#10a37f' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.title} />
          </MenuItem>
        ))}
      </Menu>

      {/* Header */}
      <div className="chatgpt-header">
        <Typography 
          variant="h5" 
          sx={{ 
            fontWeight: 600, 
            background: 'linear-gradient(135deg, #10a37f 0%, #08d17a 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 0.5 
          }}
        >
          🤖 AI Coordination Agent
        </Typography>
        <Typography variant="body2" sx={{ color: '#9ca3af', fontSize: '14px' }}>
          Universal Employee & Project Management System
        </Typography>
      </div>

      {/* Main Chat Area */}
      <div className="chatgpt-main">
        <div className="chatgpt-messages">
          {showWelcome && (
            <Fade in={showWelcome}>
              <div className="welcome-container">
                <LightbulbOutlined sx={{ fontSize: 48, mb: 2, opacity: 0.9, color: '#10a37f' }} />
                <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
                  How can I help you today?
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9, mb: 3, maxWidth: 600, mx: 'auto' }}>
                  Ask me about any employee, project tasks, team performance, or company insights. I can help you manage and analyze your team's work efficiently.
                </Typography>
                
                <div className="quick-actions">
                  {predefinedPrompts.map((prompt, index) => (
                    <Chip
                      key={index}
                      className="action-chip"
                      label={prompt.label}
                      icon={React.cloneElement(prompt.icon, { sx: { color: '#e1e5e9 !important' } })}
                      onClick={() => handleQuickAction(prompt.prompt)}
                      sx={{ cursor: 'pointer' }}
                    />
                  ))}
                </div>
              </div>
            </Fade>
          )}

          {messages.map(renderMessage)}
          {isAnalyzing && renderTypingIndicator()}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="chatgpt-input-area">
          <div className="chatgpt-input-container">
            <textarea
              ref={inputRef}
              className="chatgpt-input"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about any employee, project tasks, team performance, or company insights..."
              rows="1"
              style={{ 
                minHeight: '20px',
                maxHeight: '120px',
                overflow: 'auto',
                resize: 'none'
              }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
            />
            <IconButton
              className="send-button"
              onClick={handleSend}
              disabled={!inputMessage.trim() || isAnalyzing}
              size="small"
            >
              <Send sx={{ fontSize: 18 }} />
            </IconButton>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatGPT