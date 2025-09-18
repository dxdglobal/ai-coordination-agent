import React from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  FolderOpen as ProjectIcon,
  Assignment as TaskIcon,
  Chat as ChatIcon,
  IntegrationInstructions as IntegrationsIcon,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'

const Navbar = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
    { label: 'Projects', path: '/projects', icon: <ProjectIcon /> },
    { label: 'Tasks', path: '/tasks', icon: <TaskIcon /> },
    { label: 'AI Chat', path: '/chat', icon: <ChatIcon /> },
    { label: 'Integrations', path: '/integrations', icon: <IntegrationsIcon /> },
  ]

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Project Management System
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                backgroundColor: location.pathname === item.path ? 'rgba(255,255,255,0.1)' : 'transparent',
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar