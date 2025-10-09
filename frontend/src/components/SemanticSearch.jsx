import React, { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  TextField,
  Button,
  Box,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  Badge,
  Tooltip,
  CircularProgress,
} from '@mui/material'
import {
  Search,
  Psychology,
  Person,
  Flag,
  Star,
} from '@mui/icons-material'
import { useAPI } from '../context/APIContext'

const SemanticSearch = ({ onTaskSelect, maxHeight = '600px' }) => {
  const { taskAPI, loading, error } = useAPI()
  
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [vectorStats, setVectorStats] = useState(null)
  
  useEffect(() => {
    loadVectorStats()
  }, [])

  const loadVectorStats = async () => {
    try {
      const stats = await taskAPI.getVectorStats()
      setVectorStats(stats)
    } catch (error) {
      console.error('Failed to load vector stats:', error)
    }
  }

  const handleSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)
    try {
      const result = await taskAPI.semanticSearch(query, 10)
      setResults(result.results || [])
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch()
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      'todo': 'default',
      'in_progress': 'primary',
      'review': 'warning',
      'done': 'success',
      'blocked': 'error'
    }
    return colors[status] || 'default'
  }

  const getPriorityColor = (priority) => {
    const colors = {
      'low': 'default',
      'medium': 'primary',
      'high': 'warning',
      'urgent': 'error'
    }
    return colors[priority] || 'default'
  }

  return (
    <Card sx={{ height: '100%', maxHeight, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Psychology color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6" component="h2">
            Semantic Task SearchHHHH
          </Typography>
          {vectorStats && (
            <Chip 
              size="small" 
              label={`${vectorStats.task_embeddings || 0} indexed`} 
              sx={{ ml: 'auto' }}
              color="success"
              variant="outlined"
            />
          )}
        </Box>

        {/* Search Input */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Search tasks with natural language (e.g., 'Find urgent database tasks')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading || isSearching}
            InputProps={{
              startAdornment: <Search sx={{ color: 'action.active', mr: 1 }} />,
            }}
          />
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={!query.trim() || loading || isSearching}
            sx={{ minWidth: 'auto', px: 2 }}
          >
            {isSearching ? <CircularProgress size={20} /> : 'Search'}
          </Button>
        </Box>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Search Results */}
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          {results.length > 0 ? (
            <List dense>
              {results.map((task, index) => (
                <ListItem
                  key={task.id}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                      cursor: 'pointer'
                    }
                  }}
                  onClick={() => onTaskSelect?.(task)}
                >
                  <ListItemIcon>
                    <Badge badgeContent={index + 1} color="primary">
                      <Star sx={{ color: 'warning.main' }} />
                    </Badge>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                          {task.title}
                        </Typography>
                        <Tooltip title={`Relevance: ${(task.relevance_score * 100).toFixed(1)}%`}>
                          <Chip 
                            size="small" 
                            label={`${(task.relevance_score * 100).toFixed(0)}%`}
                            color="success"
                            variant="outlined"
                          />
                        </Tooltip>
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {task.description?.length > 100 
                            ? `${task.description.substring(0, 100)}...` 
                            : task.description || 'No description'
                          }
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          <Chip 
                            size="small" 
                            label={task.status?.replace('_', ' ') || 'Unknown'} 
                            color={getStatusColor(task.status)}
                          />
                          <Chip 
                            size="small" 
                            label={task.priority || 'Medium'} 
                            color={getPriorityColor(task.priority)}
                            variant="outlined"
                          />
                          {task.assignee && (
                            <Chip 
                              size="small" 
                              icon={<Person />} 
                              label={task.assignee} 
                              variant="outlined"
                            />
                          )}
                          {task.project_name && (
                            <Chip 
                              size="small" 
                              label={task.project_name} 
                              variant="outlined"
                              color="secondary"
                            />
                          )}
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : query && !isSearching ? (
            <Alert severity="info">
              No tasks found for "{query}". Try different keywords or use the quick searches above.
            </Alert>
          ) : !isSearching && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Psychology sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Search tasks using natural language
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try queries like "urgent security tasks", "design work for mobile", or "overdue database tasks"
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  )
}

export default SemanticSearch