import React, { useState, useEffect } from 'react'
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
} from '@mui/material'
import {
  Assignment,
  CheckCircle,
  Schedule,
  Warning,
  TrendingUp,
  AutoAwesome,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'

const Dashboard = () => {
  const { statsAPI, aiAPI, taskAPI, loading, error } = useAPI()
  const [stats, setStats] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [recentTasks, setRecentTasks] = useState([])

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      // Load overview statistics
      const statsData = await statsAPI.getOverview()
      setStats(statsData)

      // Load AI suggestions
      const suggestionsData = await aiAPI.getSuggestions()
      setSuggestions(suggestionsData)

      // Load recent tasks
      const tasksData = await taskAPI.getAll({ limit: 5 })
      setRecentTasks(tasksData)
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'done': return 'success'
      case 'in_progress': return 'primary'
      case 'review': return 'warning'
      case 'blocked': return 'error'
      default: return 'default'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'error'
      case 'high': return 'warning'
      case 'medium': return 'primary'
      case 'low': return 'default'
      default: return 'default'
    }
  }

  const getSuggestionIcon = (type) => {
    switch (type) {
      case 'overdue_tasks': return <Warning color="error" />
      case 'stalled_tasks': return <Schedule color="warning" />
      case 'unassigned_tasks': return <Assignment color="primary" />
      default: return <AutoAwesome />
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ width: '100%', mt: 2 }}>
          <LinearProgress />
        </Box>
      </Container>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#0f0f0f', pt: 8, pb: 4 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" gutterBottom sx={{ color: '#ffffff', mb: 4 }}>
          Dashboard
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Statistics Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ backgroundColor: '#1a1a1a', border: '1px solid #333333' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Assignment sx={{ mr: 2, color: '#ffffff' }} />
                  <Box>
                    <Typography sx={{ color: '#888888' }} gutterBottom>
                      Total Projects
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#ffffff' }}>
                      {stats?.total_projects || 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ backgroundColor: '#1a1a1a', border: '1px solid #333333' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Assignment sx={{ mr: 2, color: '#ffffff' }} />
                  <Box>
                    <Typography sx={{ color: '#888888' }} gutterBottom>
                      Total Tasks
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#ffffff' }}>
                      {stats?.total_tasks || 0}
                    </Typography>
                  </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircle sx={{ mr: 2, color: 'success.main' }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Completed
                  </Typography>
                  <Typography variant="h5">
                    {stats?.completed_tasks || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingUp sx={{ mr: 2, color: 'secondary.main' }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Completion Rate
                  </Typography>
                  <Typography variant="h5">
                    {stats?.completion_rate?.toFixed(1) || 0}%
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={stats?.completion_rate || 0}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ width: '100%' }}>
        {/* Recent Tasks */}
        <Grid item xs={12} md={8} sx={{ width: { xs: '100%', md: '66.666%' } }}>
          <Paper sx={{ p: 2, height: 'fit-content' }}>
            <Typography variant="h6" gutterBottom>
              Recent Tasks
            </Typography>
            {recentTasks.length === 0 ? (
              <Typography color="textSecondary">
                No recent tasks found.
              </Typography>
            ) : (
              <List>
                {recentTasks.slice(0, 5).map((task) => (
                  <ListItem key={task.id}>
                    <ListItemText
                      primary={task.title}
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                          <Chip
                            label={task.status?.replace('_', ' ')}
                            size="small"
                            color={getStatusColor(task.status)}
                          />
                          <Chip
                            label={task.priority}
                            size="small"
                            color={getPriorityColor(task.priority)}
                            variant="outlined"
                          />
                          {task.assignee && (
                            <Chip
                              label={task.assignee}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
            <Button
              variant="outlined"
              sx={{ mt: 1 }}
              onClick={() => window.location.href = '/tasks'}
            >
              View All Tasks
            </Button>
          </Paper>
        </Grid>

        {/* AI Suggestions */}
        <Grid item xs={12} md={4} sx={{ width: { xs: '100%', md: '33.333%' } }}>
          <Paper sx={{ p: 2, height: 'fit-content' }}>
            <Typography variant="h6" gutterBottom>
              AI Coordination Suggestions
            </Typography>
            {suggestions.length === 0 ? (
              <Typography color="textSecondary">
                No suggestions at this time. Everything looks good!
              </Typography>
            ) : (
              <List>
                {suggestions.slice(0, 5).map((suggestion, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {getSuggestionIcon(suggestion.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={suggestion.message}
                      secondary={
                        <Chip
                          label={suggestion.priority}
                          size="small"
                          color={suggestion.priority === 'high' ? 'error' : 'default'}
                        />
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
            <Button
              variant="outlined"
              startIcon={<AutoAwesome />}
              sx={{ mt: 1 }}
              onClick={() => window.location.href = '/chat'}
            >
              Chat with AI Agent
            </Button>
          </Paper>
        </Grid>
      </Grid>
      </Container>
    </Box>
  )
}

export default Dashboard