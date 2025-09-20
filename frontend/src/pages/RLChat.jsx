import React from 'react'
import { Box, Typography, Paper } from '@mui/material'
import EnhancedChat from '../components/EnhancedChat'

const RLChat = () => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#0f0f0f',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 3,
          borderBottom: '1px solid #333333',
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h4"
          sx={{
            color: '#ffffff',
            fontWeight: 600,
            mb: 1,
          }}
        >
          🧠 Reinforcement Learning AI Chat
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#888888',
            maxWidth: 600,
            mx: 'auto',
          }}
        >
          Experience AI that learns from your feedback using reinforcement learning. 
          Your interactions help train the AI to provide better responses over time.
        </Typography>
      </Box>

      {/* Main Chat Area */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          p: 2,
        }}
      >
        <Paper
          sx={{
            width: '100%',
            maxWidth: 1200,
            height: 'calc(100vh - 200px)',
            backgroundColor: '#1a1a1a',
            border: '1px solid #333333',
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          <EnhancedChat />
        </Paper>
      </Box>
    </Box>
  )
}

export default RLChat