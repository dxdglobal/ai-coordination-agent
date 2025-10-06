import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Box } from '@mui/material'
import GrokNavigation from './components/GrokNavigation'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/DashboardEnhanced'
import Projects from './pages/Projects'
import Tasks from './pages/Tasks'
import ChatReal from './pages/ChatReal'
import ChatGPT from './pages/ChatGPT'
import RLChat from './pages/RLChat'
import Integrations from './pages/Integrations'
import EnhancedChatbot from './components/EnhancedChatbot'
import { APIProvider } from './context/APIContext'
import { AuthProvider } from './context/AuthContext'

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#ffffff',
    },
    secondary: {
      main: '#888888',
    },
    background: {
      default: '#0f0f0f',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#888888',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 24,
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 24,
            backgroundColor: '#1a1a1a',
            '& fieldset': {
              borderColor: '#333333',
            },
            '&:hover fieldset': {
              borderColor: '#555555',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#ffffff',
            },
          },
        },
      },
    },
  },
})

function App() {
  const lightTheme = createTheme({
    palette: {
      mode: 'light',
      primary: {
        main: '#10a37f',
      },
      secondary: {
        main: '#718096',
      },
      background: {
        default: '#ffffff',
        paper: '#ffffff',
      },
      text: {
        primary: '#2d3748',
        secondary: '#718096',
      },
    },
  });

  return (
    <Router>
      <AuthProvider>
        <APIProvider>
          <Routes>
            {/* Login Route - No authentication required */}
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <EnhancedChatbot />
              </ProtectedRoute>
            } />
            
            {/* ChatGPT Style with light theme */}
            <Route path="/chatgpt" element={
              <ProtectedRoute>
                <ThemeProvider theme={lightTheme}>
                  <CssBaseline />
                  <ChatGPT />
                </ThemeProvider>
              </ProtectedRoute>
            } />
            
            {/* Other routes with dark theme and navigation */}
            <Route path="/chat-real" element={
              <ProtectedRoute>
                <ThemeProvider theme={theme}>
                  <CssBaseline />
                  <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: '#0f0f0f' }}>
                    <GrokNavigation />
                    <ChatReal />
                  </Box>
                </ThemeProvider>
              </ProtectedRoute>
            } />
            
            <Route path="/rl-chat" element={
              <ProtectedRoute>
                <ThemeProvider theme={theme}>
                  <CssBaseline />
                  <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: '#0f0f0f' }}>
                    <GrokNavigation />
                    <RLChat />
                  </Box>
                </ThemeProvider>
              </ProtectedRoute>
            } />
            
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <ThemeProvider theme={theme}>
                  <CssBaseline />
                  <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: '#0f0f0f' }}>
                    <GrokNavigation />
                    <Dashboard />
                  </Box>
                </ThemeProvider>
              </ProtectedRoute>
            } />
            
            <Route path="/projects" element={
              <ProtectedRoute>
                <ThemeProvider theme={theme}>
                  <CssBaseline />
                  <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: '#0f0f0f' }}>
                    <GrokNavigation />
                    <Projects />
                  </Box>
                </ThemeProvider>
              </ProtectedRoute>
            } />
            
            <Route path="/tasks" element={
              <ProtectedRoute>
                <ThemeProvider theme={theme}>
                  <CssBaseline />
                  <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: '#0f0f0f' }}>
                    <GrokNavigation />
                    <Tasks />
                  </Box>
                </ThemeProvider>
              </ProtectedRoute>
            } />
            
            <Route path="/integrations" element={
              <ProtectedRoute>
                <ThemeProvider theme={theme}>
                  <CssBaseline />
                  <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: '#0f0f0f' }}>
                    <GrokNavigation />
                    <Integrations />
                  </Box>
                </ThemeProvider>
              </ProtectedRoute>
            } />
          </Routes>
        </APIProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
