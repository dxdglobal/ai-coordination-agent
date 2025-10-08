import React, { useState, useContext, useEffect } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  InputAdornment,
  IconButton,
  Checkbox,
  FormControlLabel,
} from '@mui/material'
import {
  Visibility,
  VisibilityOff,
  AccountCircle,
  Lock,
  Business,
} from '@mui/icons-material'
import { AuthContext } from '../context/AuthContext'

const Login = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [savePassword, setSavePassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const { login, isAuthenticated } = useContext(AuthContext)
  const navigate = useNavigate()

  // Load saved credentials on component mount
  useEffect(() => {
    const savedCredentials = localStorage.getItem('savedLoginCredentials')
    if (savedCredentials) {
      const { username, password } = JSON.parse(savedCredentials)
      setCredentials({ username, password })
      setSavePassword(true)
    }
  }, [])

  // Save/remove credentials when savePassword changes
  useEffect(() => {
    if (savePassword && credentials.username && credentials.password) {
      localStorage.setItem('savedLoginCredentials', JSON.stringify(credentials))
    } else if (!savePassword) {
      localStorage.removeItem('savedLoginCredentials')
    }
  }, [savePassword, credentials])

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleInputChange = (e) => {
    const newCredentials = {
      ...credentials,
      [e.target.name]: e.target.value
    }
    setCredentials(newCredentials)
    
    // Clear error when user starts typing
    if (error) setError('')
    
    // If user clears the fields and savePassword is checked, uncheck it
    if (savePassword && (!newCredentials.username || !newCredentials.password)) {
      setSavePassword(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await login(credentials.username, credentials.password)
      
      // Save credentials if checkbox is checked
      if (savePassword) {
        localStorage.setItem('savedLoginCredentials', JSON.stringify(credentials))
      } else {
        localStorage.removeItem('savedLoginCredentials')
      }
      
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2,
      }}
    >
      <Container maxWidth="sm">
        <Card
          elevation={24}
          sx={{
            borderRadius: 4,
            background: 'rgba(26, 26, 26, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <CardContent sx={{ padding: 4 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Business
                sx={{
                  fontSize: 48,
                  color: '#10a37f',
                  mb: 2,
                }}
              />
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 700,
                  color: '#ffffff',
                  mb: 1,
                }}
              >
                AI Coordination Agent
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: '#888888',
                  mb: 3,
                }}
              >
                Intelligent Project Management System
              </Typography>
            </Box>

            {/* Error Alert */}
            {error && (
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 3,
                  backgroundColor: 'rgba(211, 47, 47, 0.1)',
                  color: '#f44336',
                  border: '1px solid rgba(211, 47, 47, 0.3)',
                }}
              >
                {error}
              </Alert>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit}>
              <Box sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  name="username"
                  label="Username"
                  variant="outlined"
                  value={credentials.username}
                  onChange={handleInputChange}
                  disabled={loading}
                  required
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <AccountCircle sx={{ color: '#888888' }} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      color: '#10a37f',
                      '& fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                      },
                      '&:hover fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: '#10a37f',
                      },
                    },
                    '& .MuiInputLabel-root': {
                      color: '#888888',
                    },
                    '& .MuiInputLabel-root.Mui-focused': {
                      color: '#10a37f',
                    },
                  }}
                />
              </Box>

              <Box sx={{ mb: 4 }}>
                <TextField
                  fullWidth
                  name="password"
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  variant="outlined"
                  value={credentials.password}
                  onChange={handleInputChange}
                  disabled={loading}
                  required
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Lock sx={{ color: '#888888' }} />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={togglePasswordVisibility}
                          edge="end"
                          sx={{ color: '#888888' }}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      color: '#10a37f',
                      '& fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                      },
                      '&:hover fieldset': {
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: '#10a37f',
                      },
                    },
                    '& .MuiInputLabel-root': {
                      color: '#888888',
                    },
                    '& .MuiInputLabel-root.Mui-focused': {
                      color: '#10a37f',
                    },
                  }}
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={savePassword}
                      onChange={(e) => setSavePassword(e.target.checked)}
                      sx={{
                        color: '#888888',
                        '&.Mui-checked': {
                          color: '#10a37f',
                        },
                      }}
                    />
                  }
                  label={
                    <Typography
                      variant="body2"
                      sx={{
                        color: '#888888',
                        fontSize: '0.875rem',
                      }}
                    >
                      Save Password
                    </Typography>
                  }
                />
              </Box>

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading || !credentials.username || !credentials.password}
                sx={{
                  height: 56,
                  borderRadius: 2,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #10a37f 0%, #0d8f6b 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #0d8f6b 0%, #0a7558 100%)',
                  },
                  '&:disabled': {
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: 'rgba(255, 255, 255, 0.3)',
                  },
                }}
              >
                {loading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <CircularProgress size={20} sx={{ color: 'white' }} />
                    Signing in...
                  </Box>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>

            {/* Footer */}
            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Typography
                variant="caption"
                sx={{
                  color: '#666666',
                  fontSize: '0.875rem',
                }}
              >
                Secure access to your coordination dashboard
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* Demo Credentials */}
        <Paper
          sx={{
            mt: 3,
            p: 2,
            backgroundColor: 'rgba(26, 26, 26, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: '#888888',
              textAlign: 'center',
              mb: 1,
            }}
          >
            Demo Credentials:
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: '#10a37f',
              textAlign: 'center',
              fontFamily: 'monospace',
            }}
          >
            Username: admin | Password: admin123
          </Typography>
        </Paper>
      </Container>
    </Box>
  )
}

export default Login