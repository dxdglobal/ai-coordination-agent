import React, { useState, useEffect, useRef } from 'react'
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse,
  Divider,
  LinearProgress,
  Autocomplete,
  Tabs,
  Tab,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Avatar,
  InputAdornment,
  CircularProgress,
} from '@mui/material'
import {
  Comment,
  Person,
  Schedule,
  Flag,
  ExpandLess,
  ExpandMore,
  FilterList,
  Psychology,
  Send,
  SmartToy,
  Chat,
} from '@mui/icons-material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { useAPI } from '../context/APIContext'
import SemanticSearch from '../components/SemanticSearch'

const Tasks = () => {
  const { taskAPI, projectAPI, loading, error, setError } = useAPI()
  const [tasks, setTasks] = useState([])
  const [projects, setProjects] = useState([])
  const [openComments, setOpenComments] = useState({})
  const [selectedTask, setSelectedTask] = useState(null)
  const [comments, setComments] = useState({})
  const [newComment, setNewComment] = useState('')
  const [currentTab, setCurrentTab] = useState(0)
  const [filters, setFilters] = useState({
    project_id: '',
    status: '',
    assignee: '',
    search: '',
  })

  // Chat system state
  const [chatMessages, setChatMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const chatEndRef = useRef(null)

  const statusOptions = [
    { value: 'todo', label: 'To Do', color: 'default' },
    { value: 'in_progress', label: 'In Progress', color: 'primary' },
    { value: 'review', label: 'In Review', color: 'warning' },
    { value: 'done', label: 'Done', color: 'success' },
    { value: 'blocked', label: 'Blocked', color: 'error' },
  ]

  const priorityOptions = [
    { value: 'low', label: 'Low', color: 'default' },
    { value: 'medium', label: 'Medium', color: 'primary' },
    { value: 'high', label: 'High', color: 'warning' },
    { value: 'urgent', label: 'Urgent', color: 'error' },
  ]

  useEffect(() => {
    loadTasks()
    loadProjects()
  }, [filters])

  const loadTasks = async () => {
    try {
      const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, value]) => value !== '')
      )
      const data = await taskAPI.getAll(cleanFilters)
      setTasks(data)
    } catch (err) {
      console.error('Failed to load tasks:', err)
    }
  }

  const loadProjects = async () => {
    try {
      const data = await projectAPI.getAll()
      setProjects(data)
    } catch (err) {
      console.error('Failed to load projects:', err)
    }
  }

  const loadComments = async (taskId) => {
    try {
      const data = await taskAPI.getComments(taskId)
      setComments(prev => ({ ...prev, [taskId]: data }))
    } catch (err) {
      console.error('Failed to load comments:', err)
    }
  }

  const handleAddComment = async (taskId) => {
    if (!newComment.trim()) return
    
    try {
      await taskAPI.addComment(taskId, { content: newComment })
      setNewComment('')
      await loadComments(taskId)
    } catch (err) {
      console.error('Failed to add comment:', err)
    }
  }

  const toggleComments = async (taskId) => {
    if (openComments[taskId]) {
      setOpenComments(prev => ({ ...prev, [taskId]: false }))
    } else {
      setOpenComments(prev => ({ ...prev, [taskId]: true }))
      if (!comments[taskId]) {
        await loadComments(taskId)
      }
    }
  }

  const getStatusColor = (status) => {
    const statusObj = statusOptions.find(s => s.value === status)
    return statusObj ? statusObj.color : 'default'
  }

  const getPriorityColor = (priority) => {
    const priorityObj = priorityOptions.find(p => p.value === priority)
    return priorityObj ? priorityObj.color : 'default'
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString()
  }

  const formatDuration = (hours) => {
    if (!hours) return 'Not set'
    return `${hours}h`
  }

  // Chat system functions
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatMessages])

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || isChatLoading) return

    const userMessage = {
      id: Date.now(),
      text: currentMessage,
      isUser: true,
      timestamp: new Date()
    }

    setChatMessages(prev => [...prev, userMessage])
    setCurrentMessage('')
    setIsChatLoading(true)

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentMessage,
          context: {
            tasks: tasks,
            projects: projects,
            selectedTask: selectedTask
          }
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const aiMessage = {
          id: Date.now() + 1,
          text: data.response,
          isUser: false,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, aiMessage])
      } else {
        throw new Error('Failed to get AI response')
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date(),
        isError: true
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">Tasks</Typography>
          <Typography variant="body2" color="text.secondary">
            View and manage task information
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Paper sx={{ mb: 3 }}>
          <Tabs 
            value={currentTab} 
            onChange={(e, newValue) => {
              setCurrentTab(newValue)
              if (newValue === 0) {
                setSelectedTask(null)
              }
            }}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab 
              icon={<FilterList />} 
              label="Traditional Search" 
              iconPosition="start"
            />
            <Tab 
              icon={<Psychology />} 
              label="Semantic Search" 
              iconPosition="start"
            />
            <Tab 
              icon={<SmartToy />} 
              label="AI Coordinator" 
              iconPosition="start"
            />
          </Tabs>
        </Paper>

        {currentTab === 0 && (
          <>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>Filters</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Autocomplete
                      options={projects}
                      getOptionLabel={(option) => option.name || ''}
                      value={projects.find(p => p.id === filters.project_id) || null}
                      onChange={(e, newValue) => setFilters({ ...filters, project_id: newValue?.id || '' })}
                      renderInput={(params) => <TextField {...params} label="Project" variant="outlined" />}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth variant="outlined">
                      <InputLabel>Status</InputLabel>
                      <Select
                        value={filters.status}
                        label="Status"
                        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                      >
                        <MenuItem value="">All Statuses</MenuItem>
                        {statusOptions.map((status) => (
                          <MenuItem key={status.value} value={status.value}>
                            {status.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      label="Assignee"
                      variant="outlined"
                      fullWidth
                      value={filters.assignee}
                      onChange={(e) => setFilters({ ...filters, assignee: e.target.value })}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      label="Search"
                      variant="outlined"
                      fullWidth
                      value={filters.search}
                      onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LinearProgress sx={{ width: '100%', maxWidth: 400 }} />
              </Box>
            ) : tasks.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No tasks found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Tasks will appear here when they are available
                </Typography>
              </Box>
            ) : (
              <Grid container spacing={3}>
                {tasks.map((task) => (
                  <Grid item xs={12} sm={6} md={4} key={task.id}>
                    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Typography gutterBottom variant="h6" component="div">
                          {task.title}
                        </Typography>
                        
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {task.description || 'No description'}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                          <Chip
                            label={task.status?.replace('_', ' ')}
                            color={getStatusColor(task.status)}
                            size="small"
                          />
                          {task.priority && (
                            <Chip
                              label={task.priority}
                              color={getPriorityColor(task.priority)}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                        
                        <List dense>
                          {task.assignee && (
                            <ListItem sx={{ px: 0 }}>
                              <ListItemIcon sx={{ minWidth: 32 }}>
                                <Person fontSize="small" />
                              </ListItemIcon>
                              <ListItemText 
                                primary={task.assignee}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          )}
                          
                          <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 32 }}>
                              <Schedule fontSize="small" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={`Est: ${formatDuration(task.estimated_hours)} | Actual: ${formatDuration(task.actual_hours)}`}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        </List>
                      </CardContent>
                      
                      <Divider />
                      
                      <CardActions>
                        <Button 
                          size="small" 
                          startIcon={<Comment />}
                          onClick={() => toggleComments(task.id)}
                        >
                          Comments ({task.comment_count || 0})
                          {openComments[task.id] ? <ExpandLess /> : <ExpandMore />}
                        </Button>
                      </CardActions>
                      
                      <Collapse in={openComments[task.id]} timeout="auto" unmountOnExit>
                        <CardContent sx={{ pt: 0 }}>
                          <Divider sx={{ mb: 2 }} />
                          <Typography variant="subtitle2" gutterBottom>
                            Comments
                          </Typography>
                          
                          {comments[task.id]?.map((comment) => (
                            <Box key={comment.id} sx={{ mb: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                              <Typography variant="body2">
                                {comment.content}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {formatDate(comment.created_at)}
                              </Typography>
                            </Box>
                          ))}
                          
                          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                            <TextField
                              size="small"
                              fullWidth
                              placeholder="Add a comment..."
                              value={newComment}
                              onChange={(e) => setNewComment(e.target.value)}
                              onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                  handleAddComment(task.id)
                                }
                              }}
                            />
                            <Button 
                              size="small"
                              variant="outlined"
                              onClick={() => handleAddComment(task.id)}
                              disabled={!newComment.trim()}
                            >
                              Add
                            </Button>
                          </Box>
                        </CardContent>
                      </Collapse>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </>
        )}

        {currentTab === 1 && (
          <Box sx={{ minHeight: '400px' }}>
            {/* Semantic Search - Full Width */}
            <Box sx={{ mb: 3 }}>
              <SemanticSearch 
                onTaskSelect={(task) => {
                  setSelectedTask(task)
                }} 
                maxHeight="calc(100vh - 350px)"
              />
            </Box>
            
            {/* Selected Task Details - Full Width */}
            {selectedTask ? (
              <Card sx={{ width: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Selected Task Details
                  </Typography>
                  <Typography variant="h5" gutterBottom>
                    {selectedTask.title}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {selectedTask.description || 'No description available'}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip
                      label={selectedTask.status?.replace('_', ' ')}
                      color={getStatusColor(selectedTask.status)}
                    />
                    {selectedTask.priority && (
                      <Chip
                        label={selectedTask.priority}
                        color={getPriorityColor(selectedTask.priority)}
                        variant="outlined"
                      />
                    )}
                  </Box>
                  
                  <List>
                    {selectedTask.assignee && (
                      <ListItem>
                        <ListItemIcon><Person /></ListItemIcon>
                        <ListItemText primary="Assignee" secondary={selectedTask.assignee} />
                      </ListItem>
                    )}
                    <ListItem>
                      <ListItemIcon><Schedule /></ListItemIcon>
                      <ListItemText 
                        primary="Time Tracking" 
                        secondary={`Estimated: ${formatDuration(selectedTask.estimated_hours)} | Actual: ${formatDuration(selectedTask.actual_hours)}`}
                      />
                    </ListItem>
                    {selectedTask.project_name && (
                      <ListItem>
                        <ListItemIcon><Flag /></ListItemIcon>
                        <ListItemText primary="Project" secondary={selectedTask.project_name} />
                      </ListItem>
                    )}
                  </List>
                </CardContent>
              </Card>
            ) : (
              <Card sx={{ textAlign: 'center', py: 8, width: '100%' }}>
                <CardContent>
                  <Psychology sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    Select a task from semantic search
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Use the semantic search panel to find tasks with natural language,
                    then click on a task to view its details here.
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Box>
        )}

        {currentTab === 2 && (
          <Box sx={{ minHeight: '600px' }}>
            {/* AI Coordinator Chat */}
            <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ borderBottom: 1, borderColor: 'divider', pb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <SmartToy />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      AI Coordinator
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Ask me anything about your tasks and projects
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
              
              {/* Chat Messages */}
              <CardContent sx={{ 
                flex: 1, 
                overflow: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                maxHeight: '400px'
              }}>
                {chatMessages.length === 0 ? (
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    height: '100%',
                    color: 'text.secondary'
                  }}>
                    <Chat sx={{ fontSize: 64, mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Start a conversation
                    </Typography>
                    <Typography variant="body2" textAlign="center">
                      Ask me about your tasks, project status, deadlines, or anything else you need help with.
                    </Typography>
                  </Box>
                ) : (
                  chatMessages.map((message) => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        justifyContent: message.isUser ? 'flex-end' : 'flex-start',
                        mb: 1
                      }}
                    >
                      <Box
                        sx={{
                          maxWidth: '70%',
                          padding: 2,
                          borderRadius: 2,
                          backgroundColor: message.isUser 
                            ? 'primary.main' 
                            : message.isError 
                              ? 'error.light'
                              : 'grey.100',
                          color: message.isUser ? 'white' : 'text.primary'
                        }}
                      >
                        <Typography variant="body1">
                          {message.text}
                        </Typography>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            opacity: 0.7,
                            display: 'block',
                            mt: 0.5
                          }}
                        >
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Box>
                    </Box>
                  ))
                )}
                <div ref={chatEndRef} />
              </CardContent>
              
              {/* Chat Input */}
              <CardContent sx={{ borderTop: 1, borderColor: 'divider', pt: 2 }}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    fullWidth
                    multiline
                    maxRows={3}
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me about your tasks..."
                    variant="outlined"
                    size="small"
                    disabled={isChatLoading}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          {isChatLoading && <CircularProgress size={20} />}
                        </InputAdornment>
                      )
                    }}
                  />
                  <IconButton
                    color="primary"
                    onClick={handleSendMessage}
                    disabled={!currentMessage.trim() || isChatLoading}
                    sx={{ alignSelf: 'flex-end' }}
                  >
                    <Send />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}
      </Container>
    </LocalizationProvider>
  )
}

export default Tasks