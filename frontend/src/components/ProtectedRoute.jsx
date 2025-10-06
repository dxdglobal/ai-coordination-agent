import React, { useContext } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Box, CircularProgress, Typography } from '@mui/material'
import { AuthContext } from '../context/AuthContext'

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useContext(AuthContext)
  const location = useLocation()

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#0f0f0f',
          color: '#ffffff',
        }}
      >
        <CircularProgress
          size={48}
          sx={{
            color: '#10a37f',
            mb: 2,
          }}
        />
        <Typography
          variant="h6"
          sx={{
            color: '#888888',
            textAlign: 'center',
          }}
        >
          Verifying authentication...
        </Typography>
      </Box>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Render protected content
  return children
}

export default ProtectedRoute