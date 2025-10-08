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
      main: '#3b82f6', // Professional blue
      light: '#60a5fa',
      dark: '#2563eb',
    },
    secondary: {
      main: '#64748b', // Neutral slate
      light: '#94a3b8',
      dark: '#475569',
    },
    success: {
      main: '#10b981', // Professional green
      light: '#34d399',
      dark: '#059669',
    },
    warning: {
      main: '#f59e0b', // Professional amber
      light: '#fbbf24',
      dark: '#d97706',
    },
    error: {
      main: '#ef4444', // Professional red
      light: '#f87171',
      dark: '#dc2626',
    },
    info: {
      main: '#06b6d4', // Professional cyan
      light: '#22d3ee',
      dark: '#0891b2',
    },
    background: {
      default: '#0f172a', // Slate 900
      paper: '#1e293b',   // Slate 800
    },
    text: {
      primary: '#f8fafc',   // Slate 50
      secondary: '#cbd5e1', // Slate 300
    },
    divider: '#334155', // Slate 700
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
          padding: '8px 16px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          },
        },
        contained: {
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: '#1e293b',
            fontSize: '0.875rem',
            '& fieldset': {
              borderColor: '#475569',
            },
            '&:hover fieldset': {
              borderColor: '#64748b',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#3b82f6',
              borderWidth: 2,
            },
          },
          '& .MuiInputLabel-root': {
            color: '#94a3b8',
            fontSize: '0.875rem',
            '&.Mui-focused': {
              color: '#3b82f6',
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e293b',
          borderRadius: 12,
          border: '1px solid #334155',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e293b',
          backgroundImage: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e293b',
          borderBottom: '1px solid #334155',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        },
      },
    },
  },
});

function App() {
const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#3b82f6', // Professional blue
      light: '#60a5fa',
      dark: '#2563eb',
    },
    secondary: {
      main: '#64748b', // Neutral slate
      light: '#94a3b8',
      dark: '#475569',
    },
    success: {
      main: '#10b981', // Professional green
      light: '#34d399',
      dark: '#059669',
    },
    warning: {
      main: '#f59e0b', // Professional amber
      light: '#fbbf24',
      dark: '#d97706',
    },
    error: {
      main: '#ef4444', // Professional red
      light: '#f87171',
      dark: '#dc2626',
    },
    info: {
      main: '#06b6d4', // Professional cyan
      light: '#22d3ee',
      dark: '#0891b2',
    },
    background: {
      default: '#f8fafc', // Slate 50
      paper: '#ffffff',   // White
    },
    text: {
      primary: '#0f172a',   // Slate 900
      secondary: '#475569', // Slate 600
    },
    divider: '#e2e8f0', // Slate 200
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
          padding: '8px 16px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          },
        },
        contained: {
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: '#ffffff',
            fontSize: '0.875rem',
            '& fieldset': {
              borderColor: '#d1d5db',
            },
            '&:hover fieldset': {
              borderColor: '#9ca3af',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#3b82f6',
              borderWidth: 2,
            },
          },
          '& .MuiInputLabel-root': {
            color: '#6b7280',
            fontSize: '0.875rem',
            '&.Mui-focused': {
              color: '#3b82f6',
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          borderRadius: 12,
          border: '1px solid #e5e7eb',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          backgroundImage: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e5e7eb',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        },
      },
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
