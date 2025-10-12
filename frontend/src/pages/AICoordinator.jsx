import React from 'react'
import { Box } from '@mui/material'
import AICoordinatorChat from '../components/AICoordinatorChat'

const AICoordinator = () => {
  return (
    <Box sx={{ height: '100vh', overflow: 'hidden' }}>
      <AICoordinatorChat />
    </Box>
  )
}

export default AICoordinator