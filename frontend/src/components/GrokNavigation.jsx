import React, { useState, useContext } from 'react'
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
  Menu as MenuComponent,
  MenuItem,
  Chip,
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
  Logout,
  AccountCircle,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'

const GrokNavigation = () => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [userMenuAnchor, setUserMenuAnchor] = useState(null)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useContext(AuthContext)

  const menuItems = [
    { title: 'RL Chat', path: '/rl-chat', icon: <Psychology /> },
    { title: 'AI Coordinator', path: '/ai-coordinator', icon: <SmartToy /> },
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

  const handleUserMenuOpen = (event) => {
    setUserMenuAnchor(event.currentTarget)
  }

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null)
  }

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
    handleUserMenuClose()
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
          {/* User Info Section */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Avatar 
              sx={{ 
                backgroundColor: '#10a37f',
                width: 40,
                height: 40,
              }}
              onClick={handleUserMenuOpen}
            >
              {user?.name ? user.name.charAt(0).toUpperCase() : <AccountCircle />}
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" sx={{ color: '#ffffff', fontWeight: 600, fontSize: '0.95rem' }}>
                {user?.name || 'User'}
              </Typography>
              <Chip
                label={user?.role || 'Member'}
                size="small"
                sx={{
                  backgroundColor: 'rgba(16, 163, 127, 0.2)',
                  color: '#10a37f',
                  fontSize: '0.75rem',
                  height: 20,
                }}
              />
            </Box>
          </Box>

          <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600, mb: 2 }}>
            AI Coordination Agent
          </Typography>

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
                  <Help />
                </ListItemIcon>
                <ListItemText primary="Help" />
              </ListItemButton>
            </ListItem>

            <ListItem disablePadding>
              <ListItemButton
                onClick={handleLogout}
                sx={{
                  borderRadius: 2,
                  color: '#f44336',
                  '&:hover': {
                    backgroundColor: 'rgba(244, 67, 54, 0.1)',
                    color: '#f44336',
                  },
                }}
              >
                <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                  <Logout />
                </ListItemIcon>
                <ListItemText primary="Logout" />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* User Menu */}
      <MenuComponent
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
        PaperProps={{
          sx: {
            backgroundColor: '#1a1a1a',
            border: '1px solid #333333',
            minWidth: 200,
          },
        }}
      >
        <MenuItem onClick={handleUserMenuClose} sx={{ color: '#ffffff' }}>
          <ListItemIcon sx={{ color: '#888888' }}>
            <AccountCircle />
          </ListItemIcon>
          Profile
        </MenuItem>
        <MenuItem onClick={handleUserMenuClose} sx={{ color: '#ffffff' }}>
          <ListItemIcon sx={{ color: '#888888' }}>
            <Settings />
          </ListItemIcon>
          Settings
        </MenuItem>
        <Divider sx={{ borderColor: '#333333' }} />
        <MenuItem onClick={handleLogout} sx={{ color: '#f44336' }}>
          <ListItemIcon sx={{ color: '#f44336' }}>
            <Logout />
          </ListItemIcon>
          Logout
        </MenuItem>
      </MenuComponent>
    </>
  )
}

export default GrokNavigation