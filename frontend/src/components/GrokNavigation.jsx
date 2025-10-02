import React, { useState } from 'react'
import {
  Box,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Avatar,
} from '@mui/material'
import {
  Menu,
  Close,
  Dashboard,
  Assignment,
  Folder,
  IntegrationInstructions,
  SmartToy,
  Settings,
  Help,
  Psychology,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'

const GrokNavigation = () => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    { title: 'ChatGPT Style', path: '/', icon: <SmartToy /> },
    { title: 'Classic Chat', path: '/chat-real', icon: <SmartToy /> },
    { title: 'RL Chat', path: '/rl-chat', icon: <Psychology /> },
    { title: 'Dashboard', path: '/dashboard', icon: <Dashboard /> },
    { title: 'Projects', path: '/projects', icon: <Folder /> },
    { title: 'Tasks', path: '/tasks', icon: <Assignment /> },
    { title: 'Integrations', path: '/integrations', icon: <IntegrationInstructions /> },
  ]

  const handleNavigation = (path) => {
    navigate(path)
    setIsDrawerOpen(false)
  }

  const toggleDrawer = () => {
    setIsDrawerOpen(!isDrawerOpen)
  }

  return (
    <>
      {/* Menu Button - Only visible when not on main chat page or when drawer is open */}
      {(location.pathname !== '/' || isDrawerOpen) && (
        <Box
          sx={{
            position: 'fixed',
            top: 24,
            left: 24,
            zIndex: 1300,
          }}
        >
          <IconButton
            onClick={toggleDrawer}
            sx={{
              backgroundColor: 'rgba(26, 26, 26, 0.8)',
              backdropFilter: 'blur(10px)',
              color: '#ffffff',
              '&:hover': {
                backgroundColor: 'rgba(42, 42, 42, 0.8)',
              },
            }}
          >
            {isDrawerOpen ? <Close /> : <Menu />}
          </IconButton>
        </Box>
      )}

      {/* Drawer */}
      <Drawer
        anchor="left"
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        PaperProps={{
          sx: {
            width: 280,
            backgroundColor: '#0f0f0f',
            border: 'none',
            borderRight: '1px solid #333333',
          },
        }}
      >
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Avatar sx={{ backgroundColor: '#333333' }}>
              <SmartToy />
            </Avatar>
            <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
              AI Coordination Agent
            </Typography>
          </Box>

          <List sx={{ px: 0 }}>
            {menuItems.map((item) => (
              <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  onClick={() => handleNavigation(item.path)}
                  selected={location.pathname === item.path}
                  sx={{
                    borderRadius: 2,
                    color: '#ffffff',
                    '&.Mui-selected': {
                      backgroundColor: '#1a1a1a',
                      '&:hover': {
                        backgroundColor: '#2a2a2a',
                      },
                    },
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.title}
                    primaryTypographyProps={{
                      fontWeight: location.pathname === item.path ? 600 : 400,
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>

          <Divider sx={{ my: 3, borderColor: '#333333' }} />

          <List sx={{ px: 0 }}>
            <ListItem disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                sx={{
                  borderRadius: 2,
                  color: '#888888',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    color: '#ffffff',
                  },
                }}
              >
                <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                  <Settings />
                </ListItemIcon>
                <ListItemText primary="Settings" />
              </ListItemButton>
            </ListItem>
            
            <ListItem disablePadding>
              <ListItemButton
                sx={{
                  borderRadius: 2,
                  color: '#888888',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    color: '#ffffff',
                  },
                }}
              >
                <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                  <Help />
                </ListItemIcon>
                <ListItemText primary="Help" />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
      </Drawer>
    </>
  )
}

export default GrokNavigation