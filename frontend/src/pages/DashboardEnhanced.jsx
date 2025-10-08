import React, { useState, useEffect, useContext } from 'react'
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  Button,
  Avatar,
  Divider,
  IconButton,
} from '@mui/material'
import {
  Assignment,
  CheckCircle,
  Schedule,
  Warning,
  TrendingUp,
  AutoAwesome,
  Folder,
  People,
  Notifications,
  Refresh,
  TrendingDown,
  AccessTime,
  Margin,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'
import { AuthContext } from '../context/AuthContext'

const Dashboard = () => {
  const { user } = useContext(AuthContext)
  const { statsAPI, aiAPI, taskAPI, loading, error } = useAPI()
  const [stats, setStats] = useState({
    projects: { total: 0, active: 0, completed: 0 },
    tasks: { total: 0, pending: 0, completed: 0, overdue: 0 },
    users: { total: 0, active: 0 },
    performance: { completionRate: 0, avgTime: 0 }
  })
  const [recentTasks, setRecentTasks] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      // Load mock data for now - will be replaced with real API calls
      setStats({
        projects: { total: 24, active: 18, completed: 6 },
        tasks: { total: 156, pending: 42, completed: 98, overdue: 16 },
        users: { total: 12, active: 8 },
        performance: { completionRate: 78, avgTime: 4.2 }
      })

      setRecentTasks([
        {
          id: 1,
          title: 'Complete user authentication system',
          project: 'AI Coordination Agent',
          assignee: 'John Doe',
          priority: 'high',
          status: 'in_progress',
          dueDate: '2025-10-07'
        },
        {
          id: 2,
          title: 'Design database schema',
          project: 'CRM Integration',
          assignee: 'Jane Smith',
          priority: 'medium',
          status: 'pending',
          dueDate: '2025-10-09'
        },
        {
          id: 3,
          title: 'Setup CI/CD pipeline',
          project: 'DevOps Setup',
          assignee: 'Mike Johnson',
          priority: 'high',
          status: 'overdue',
          dueDate: '2025-10-03'
        }
      ])

      setSuggestions([
        'Review overdue tasks and reassign if needed',
        'Schedule team meeting for project alignment',
        'Update project documentation'
      ])

      setLastUpdate(new Date())
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#4caf50'
      case 'in_progress': return '#2196f3'
      case 'overdue': return '#f44336'
      case 'pending': return '#ff9800'
      default: return '#757575'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#f44336'
      case 'medium': return '#ff9800'
      case 'low': return '#4caf50'
      default: return '#757575'
    }
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4, pl: 5 }}>
      {/* Header */}
      <Box sx={{ mb: 4, maxWidth: '100%', margin: '0 auto 2rem auto' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 700 }}>
            Welcome back, {user?.name || 'User'}!
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadDashboardData}
              disabled={loading}
              sx={{ color: '#10a37f', borderColor: '#10a37f' }}
            >
              Refresh
            </Button>
            <IconButton sx={{ color: '#ffffff' }}>
              <Notifications />
            </IconButton>
          </Box>
        </Box>
        <Typography variant="body1" sx={{ color: '#888888' }}>
          Last updated: {lastUpdate.toLocaleTimeString()}
        </Typography>
      </Box>

      {/* Quick Stats */}
      <Box sx={{ maxWidth: '100%', margin: '0 auto', mb: 4 }}>
        <Grid container spacing={1}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              backgroundColor: '#1a1a1a', 
              border: '1px solid #333333',
              height: '140px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 700 }}>
                      {stats.projects.active}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#888888' }}>
                      Active Projects
                    </Typography>
                  </Box>
                  <Avatar sx={{ backgroundColor: '#10a37f' }}>
                    <Folder />
                  </Avatar>
                </Box>
                <Box sx={{ mt: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={(stats.projects.active / stats.projects.total) * 100}
                    sx={{
                      backgroundColor: '#333333',
                      '& .MuiLinearProgress-bar': { backgroundColor: '#10a37f' }
                    }}
                  />
                  <Typography variant="caption" sx={{ color: '#888888', mt: 1, display: 'block' }}>
                    {stats.projects.total} total projects
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              backgroundColor: '#1a1a1a', 
              border: '1px solid #333333',
              height: '140px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 700 }}>
                      {stats.tasks.pending}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#888888' }}>
                      Pending Tasks
                    </Typography>
                  </Box>
                  <Avatar sx={{ backgroundColor: '#2196f3' }}>
                    <Assignment />
                  </Avatar>
                </Box>
                <Box sx={{ mt: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={(stats.tasks.completed / stats.tasks.total) * 100}
                    sx={{
                      backgroundColor: '#333333',
                      '& .MuiLinearProgress-bar': { backgroundColor: '#2196f3' }
                    }}
                  />
                  <Typography variant="caption" sx={{ color: '#888888', mt: 1, display: 'block' }}>
                    {stats.tasks.completed} completed tasks
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              backgroundColor: '#1a1a1a', 
              border: '1px solid #333333',
              height: '140px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ color: '#f44336', fontWeight: 700 }}>
                      {stats.tasks.overdue}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#888888' }}>
                      Overdue Tasks
                    </Typography>
                  </Box>
                  <Avatar sx={{ backgroundColor: '#f44336' }}>
                    <Warning />
                  </Avatar>
                </Box>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" sx={{ color: '#f44336' }}>
                    Requires immediate attention
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              backgroundColor: '#1a1a1a', 
              border: '1px solid #333333',
              height: '140px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 700 }}>
                      {stats.performance.completionRate}%
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#888888' }}>
                      Completion Rate
                    </Typography>
                  </Box>
                  <Avatar sx={{ backgroundColor: '#4caf50' }}>
                    <TrendingUp />
                  </Avatar>
                </Box>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" sx={{ color: '#4caf50' }}>
                    +5% from last month
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Recent Tasks and AI Suggestions */}
      <Box sx={{ maxWidth: '100%', margin: '0 auto' }}>
        <Grid container spacing={1} >
          {/* Recent Tasks */}
          <Grid 
            item 
            xs={12} 
            md={8} 
            lg={8} 
            sx={{ 
              flex: '0 0 65.666%',
              maxWidth: '65.666%',
              width: '65.666%',
              '@media (max-width: 960px)': {
                flex: '0 0 100%',
                maxWidth: '100%',
                width: '100%'
              }
            }}
           
          >
            <Card
              sx={{
                backgroundColor: '#1a1a1a',
                border: '1px solid #333333',
                width: '100%',
                height: 'fit-content',
              }}
            >
              <CardContent sx={{ padding: '1.5rem !important' }} style={{ width: '100%' }}>
                <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
                  Recent Tasks
                </Typography>

                <List sx={{ width: '100%', padding: 0 }}>
                  {recentTasks.map((task, index) => (
                    <React.Fragment key={task.id}>
                      <ListItem sx={{ px: 0, py: 1, width: '100%' }}>
                        <ListItemIcon>
                          <Avatar
                            sx={{
                              backgroundColor: getStatusColor(task.status),
                              width: 32,
                              height: 32,
                            }}
                          >
                            {task.status === 'completed' ? (
                              <CheckCircle />
                            ) : task.status === 'overdue' ? (
                              <Warning />
                            ) : (
                              <AccessTime />
                            )}
                          </Avatar>
                        </ListItemIcon>

                        <ListItemText
                          sx={{ width: '100%', margin: 0 }}
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                              <Typography
                                variant="body1"
                                sx={{ color: '#ffffff', fontWeight: 500, flex: 1 }}
                              >
                                {task.title}
                              </Typography>
                              <Chip
                                label={task.priority}
                                size="small"
                                sx={{
                                  backgroundColor: `${getPriorityColor(task.priority)}20`,
                                  color: getPriorityColor(task.priority),
                                  fontWeight: 500,
                                }}
                              />
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 1, width: '100%' }}>
                              <Typography variant="body2" sx={{ color: '#888888' }}>
                                {task.project} • Assigned to {task.assignee}
                              </Typography>
                              <Typography variant="caption" sx={{ color: '#666666' }}>
                                Due: {new Date(task.dueDate).toLocaleDateString()}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>

                      {index < recentTasks.length - 1 && (
                        <Divider sx={{ borderColor: '#333333', width: '100%' }} />
                      )}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* AI Suggestions */}
          <Grid 
            item 
            xs={12} 
            md={4} 
            lg={4}
            sx={{ 
              flex: '0 0 33.333%',
              maxWidth: '33.333%',
              width: '33.333%',
              '@media (max-width: 960px)': {
                flex: '0 0 100%',
                maxWidth: '100%',
                width: '100%'
              }
            }}
          >
            <Card sx={{ backgroundColor: '#1a1a1a', border: '1px solid #333333', mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <AutoAwesome sx={{ color: '#10a37f', mr: 1 }} />
                  <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                    AI Suggestions
                  </Typography>
                </Box>
                <List>
                  {suggestions.map((suggestion, index) => (
                    <ListItem key={index} sx={{ px: 0, py: 1 }}>
                      <ListItemText
                        primary={
                          <Typography variant="body2" sx={{ color: '#ffffff' }}>
                            {suggestion}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card sx={{ backgroundColor: '#1a1a1a', border: '1px solid #333333' }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<Assignment />}
                    sx={{
                      backgroundColor: '#10a37f',
                      '&:hover': { backgroundColor: '#0d8f6b' },
                      justifyContent: 'flex-start',
                    }}
                  >
                    Create New Task
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Folder />}
                    sx={{
                      color: '#ffffff',
                      borderColor: '#333333',
                      '&:hover': { borderColor: '#555555' },
                      justifyContent: 'flex-start',
                    }}
                  >
                    New Project
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<People />}
                    sx={{
                      color: '#ffffff',
                      borderColor: '#333333',
                      '&:hover': { borderColor: '#555555' },
                      justifyContent: 'flex-start',
                    }}
                  >
                    Team Overview
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mt: 3,
            backgroundColor: 'rgba(211, 47, 47, 0.1)',
            color: '#f44336',
            border: '1px solid rgba(211, 47, 47, 0.3)',
          }}
        >
          {error}
        </Alert>
      )}
    </Container>
  )
}

export default Dashboard