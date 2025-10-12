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
import SemanticSearch from '../components/SemanticSearch'

const Tasks = () => {
  const [tasks, setTasks] = useState([])
  const [allTasks, setAllTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [currentTab, setCurrentTab] = useState(0)
  const [stats, setStats] = useState(null)
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const PAGE_SIZE = 50 // Load 50 tasks at a time
  
  // Filter states
  const [currentStatusFilter, setCurrentStatusFilter] = useState('active') // Default to active
  const [currentPriorityFilter, setCurrentPriorityFilter] = useState(null)
  const [titleSearchQuery, setTitleSearchQuery] = useState('')
  const [isSearchMode, setIsSearchMode] = useState(false)
  const [searchResults, setSearchResults] = useState(null)

  // Chat system state
  const [chatMessages, setChatMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [selectedTask, setSelectedTask] = useState(null)
  const [projects, setProjects] = useState([])
  const chatEndRef = useRef(null)

  const API_BASE_URL = 'http://127.0.0.1:5001'

  const statusOptions = [
    { value: 'not_started', label: 'Not Started', color: 'default' },
    { value: 'todo', label: 'To Do', color: 'default' },
    { value: 'in_progress', label: 'In Progress', color: 'primary' },
    { value: 'review', label: 'In Review', color: 'warning' },
    { value: 'done', label: 'Done', color: 'success' },
    { value: 'blocked', label: 'Blocked', color: 'error' },
    { value: 'urgent', label: 'Urgent', color: 'error' },
    { value: 'overdue', label: 'Overdue', color: 'error' },
  ]

  const priorityOptions = [
    { value: 'low', label: 'Low', color: 'success' },
    { value: 'medium', label: 'Medium', color: 'warning' },
    { value: 'high', label: 'High', color: 'error' },
    { value: 'urgent', label: 'Urgent', color: 'error' },
  ]

  useEffect(() => {
    loadTasksWithPagination(1, true) // Load first page
    loadTaskStats()
  }, [])

  useEffect(() => {
    // Reset pagination when filters change
    if (currentStatusFilter || currentPriorityFilter || titleSearchQuery.trim()) {
      setCurrentPage(1)
      setTasks([])
      loadTasksWithPagination(1, true)
    }
  }, [currentStatusFilter, currentPriorityFilter, titleSearchQuery])

  // Paginated task loading with server-side filtering
  const loadTasksWithPagination = async (page = 1, reset = false) => {
    try {
      if (reset) {
        setLoading(true)
        setTasks([])
        setCurrentPage(1)
      } else {
        setLoadingMore(true)
      }
      
      setError('')
      
      // Build query parameters
      const params = new URLSearchParams()
      
      // For overdue tasks, don't limit the results to show all overdue tasks
      if (currentStatusFilter === 'overdue') {
        params.append('limit', '1000') // High limit to get all overdue tasks
        params.append('offset', '0')   // Always start from beginning for overdue
      } else {
        params.append('limit', PAGE_SIZE.toString())
        params.append('offset', ((page - 1) * PAGE_SIZE).toString())
      }
      
      // Apply filters
      if (currentStatusFilter && currentStatusFilter !== 'all') {
        if (currentStatusFilter === 'active') {
          // For active filter, include not_started, todo, in_progress, review
          params.append('status', 'not_started,todo,in_progress,review')
        } else {
          params.append('status', currentStatusFilter)
        }
      }
      
      if (currentPriorityFilter && currentPriorityFilter !== 'all') {
        params.append('priority', currentPriorityFilter)
      }
      
      if (titleSearchQuery.trim()) {
        params.append('title', titleSearchQuery.trim())
      }
      
      params.append('sort_by', 'id')
      params.append('sort_order', 'DESC')
      
      const response = await fetch(`${API_BASE_URL}/api/crm/tasks/search?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.tasks) {
          console.log(`✅ Loaded page ${page}: ${data.tasks.length} tasks`)
          
          if (reset) {
            setTasks(data.tasks)
            setCurrentPage(1)
          } else {
            setTasks(prev => [...prev, ...data.tasks])
          }
          
          // Update pagination state
          if (currentStatusFilter === 'overdue') {
            // For overdue tasks, load all at once
            setHasMore(false)
            setTotalCount(data.tasks.length)
            setCurrentPage(1)
          } else {
            // Normal pagination behavior
            setHasMore(data.tasks.length === PAGE_SIZE)
            setTotalCount(data.total || data.tasks.length)
            setCurrentPage(page)
          }
          
          // Update search mode
          const hasFilters = currentStatusFilter !== 'active' || currentPriorityFilter || titleSearchQuery.trim()
          setIsSearchMode(hasFilters)
          
          return
        } else {
          throw new Error(data.error || 'Failed to fetch tasks')
        }
      } else {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
    } catch (err) {
      console.error('Failed to load tasks:', err)
      setError(`Failed to load tasks: ${err.message}`)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const loadTaskStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/crm/tasks/stats`)
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          console.log('✅ Loaded task statistics from CRM database')
          setStats(data.stats)
          return
        }
      }
      
      console.warn('Failed to load stats from CRM, using fallback')
    } catch (err) {
      console.log('Error loading task stats:', err)
    }
    
    // Fallback mock stats
    const mockStats = {
      total_tasks: 10,
      active_tasks: 6,
      completed_tasks: 2,
      overdue_tasks: 1,
      tasks_by_status: {
        todo: 2,
        in_progress: 2,
        review: 2,
        done: 2,
        blocked: 1,
        urgent: 1
      },
      tasks_by_priority: {
        low: 2,
        medium: 3,
        high: 3,
        urgent: 2
      }
    }
    
    setStats(mockStats)
  }

  const filterByStatus = (status) => {
    setCurrentStatusFilter(status)
    // Pagination will trigger reload via useEffect
  }

  // Load more tasks (pagination)
  const loadMoreTasks = () => {
    if (!loadingMore && hasMore) {
      loadTasksWithPagination(currentPage + 1, false)
    }
  }

  const filterByPriority = (priority) => {
    setCurrentPriorityFilter(priority)
    // Pagination will trigger reload via useEffect
  }

  const searchByTitle = (searchTerm) => {
    setTitleSearchQuery(searchTerm)
    // Pagination will trigger reload via useEffect with debounce
  }

  const handleClearSearch = () => {
    setIsSearchMode(false)
    setSearchResults(null)
    setCurrentStatusFilter('active') // Return to active tasks
    setCurrentPriorityFilter(null)
    setTitleSearchQuery('')
    // This will trigger reload via useEffect
  }

  const showActiveTasks = () => {
    setCurrentStatusFilter('active')
    setCurrentPriorityFilter(null)
    setTitleSearchQuery('')
    setIsSearchMode(false)
    // This will trigger reload via useEffect
  }

  const showAllTasks = () => {
    setCurrentStatusFilter('all')
    setCurrentPriorityFilter(null)
    setTitleSearchQuery('')
    setIsSearchMode(false)
    // This will trigger reload via useEffect
  }

  const showOverdueTasks = () => {
    setCurrentStatusFilter('overdue')
    setCurrentPriorityFilter(null)
    setTitleSearchQuery('')
    setIsSearchMode(true)
    // This will trigger reload via useEffect
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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, mt: 10 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h4">Tasks</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                variant={currentStatusFilter === 'active' ? "contained" : "outlined"}
                size="small"
                onClick={showActiveTasks}
                color="primary"
              >
                Active ({stats?.active_tasks || 0})
              </Button>
              <Button 
                variant={currentStatusFilter === 'all' ? "contained" : "outlined"}
                size="small"
                onClick={showAllTasks}
                color="secondary"
              >
                All ({stats?.total_tasks || 0})
              </Button>
              <Button 
                variant={currentStatusFilter === 'overdue' ? "contained" : "outlined"}
                size="small"
                onClick={showOverdueTasks}
                color="warning"
              >
                Overdue ({stats?.overdue_tasks || 0})
              </Button>
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary">
            View and manage task information • Page {currentPage} • {tasks.length} loaded
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
            onChange={(e, newValue) => setCurrentTab(newValue)}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab 
              icon={<FilterList />} 
              label="Task List" 
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
            {/* Quick Status Filters */}
            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Quick Status Filters
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                <Chip
                  label="All Tasks"
                  onClick={() => filterByStatus(null)}
                  variant={currentStatusFilter === null ? "filled" : "outlined"}
                  color="primary"
                />
                {statusOptions.map((status) => (
                  <Chip
                    key={status.value}
                    label={status.label}
                    onClick={() => filterByStatus(status.value)}
                    variant={currentStatusFilter === status.value ? "filled" : "outlined"}
                    color={status.color}
                  />
                ))}
              </Box>
            </Paper>

            {/* Priority Filters */}
            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Priority Filters
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                <Chip
                  label="All Priorities"
                  onClick={() => filterByPriority(null)}
                  variant={currentPriorityFilter === null ? "filled" : "outlined"}
                  color="primary"
                />
                {priorityOptions.map((priority) => (
                  <Chip
                    key={priority.value}
                    label={priority.label}
                    onClick={() => filterByPriority(priority.value)}
                    variant={currentPriorityFilter === priority.value ? "filled" : "outlined"}
                    color={priority.color}
                  />
                ))}
              </Box>
            </Paper>

            {/* Search by Title */}
            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Search by Task Title
              </Typography>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Enter task title to search..."
                value={titleSearchQuery}
                onChange={(e) => {
                  setTitleSearchQuery(e.target.value)
                  searchByTitle(e.target.value)
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Comment />
                    </InputAdornment>
                  ),
                  endAdornment: titleSearchQuery && (
                    <InputAdornment position="end">
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          setTitleSearchQuery('')
                          searchByTitle('')
                        }}
                      >
                        Clear
                      </Button>
                    </InputAdornment>
                  )
                }}
              />
            </Paper>

            {/* Filter Status Display */}
            <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
              <Typography variant="body2" color="textSecondary">
                <strong>
                  Showing {tasks.length} 
                  {currentStatusFilter === 'active' ? ' active' : 
                   currentStatusFilter === 'all' ? ' total' :
                   currentStatusFilter === 'overdue' ? ' overdue' :
                   isSearchMode ? ' filtered' : ''} tasks
                </strong>
                {isSearchMode && (
                  <>
                    {currentStatusFilter && currentStatusFilter !== 'active' && currentStatusFilter !== 'all' && (
                      <span> • Status: {statusOptions.find(s => s.value === currentStatusFilter)?.label}</span>
                    )}
                    {currentPriorityFilter && (
                      <span> • Priority: {priorityOptions.find(p => p.value === currentPriorityFilter)?.label}</span>
                    )}
                    {titleSearchQuery && (
                      <span> • Title contains: "{titleSearchQuery}"</span>
                    )}
                  </>
                )}
                {(isSearchMode || currentStatusFilter === 'all' || currentStatusFilter === 'overdue') && (
                  <Button
                    size="small"
                    onClick={isSearchMode ? handleClearSearch : showActiveTasks}
                    sx={{ ml: 2 }}
                  >
                    {isSearchMode ? 'Clear Filters' : 'Show Active Tasks'}
                  </Button>
                )}
                
                {hasMore && (
                  <span> • Page {currentPage} • More available</span>
                )}
                {!hasMore && tasks.length > 0 && (
                  <span> • All loaded</span>
                )}
              </Typography>
            </Paper>

            {/* Statistics Cards */}
            {stats && !isSearchMode && (
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Schedule sx={{ color: 'primary.main', mr: 2 }} />
                        <Box>
                          <Typography variant="h4">{stats.total_tasks}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Total Tasks
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
                        <Flag sx={{ color: 'success.main', mr: 2 }} />
                        <Box>
                          <Typography variant="h4">{stats.active_tasks}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Active Tasks
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
                        <Person sx={{ color: 'success.main', mr: 2 }} />
                        <Box>
                          <Typography variant="h4">{stats.completed_tasks}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Completed
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 4,
                      }
                    }}
                    onClick={showOverdueTasks}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Schedule sx={{ color: 'warning.main', mr: 2 }} />
                        <Box>
                          <Typography variant="h4">{stats.overdue_tasks}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Overdue
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : tasks.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Schedule sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  {isSearchMode ? 'No tasks found matching your filters' : 'No tasks found'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {isSearchMode ? 'Try adjusting your search terms' : 'Tasks will appear here when they are available'}
                </Typography>
              </Box>
            ) : (
              <>
                {/* Task Grid */}
              <Box 
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(2, 1fr)',
                    md: 'repeat(3, 1fr)',
                    lg: 'repeat(4, 1fr)'
                  },
                  gap: 3,
                  width: '100%',
                  gridAutoRows: 'auto',
                  alignItems: 'start',
                  minHeight: 'auto',
                  maxHeight: 'none',
                  overflow: 'visible',
                  marginBottom: '0px'
                }}
              >
                {tasks.map((task) => (
                  <Card 
                    key={task.id}
                    sx={{ 
                      display: 'flex', 
                      flexDirection: 'column',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      minHeight: 'auto',
                      height: 'auto',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 4,
                      }
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Typography gutterBottom variant="h6" component="div" sx={{ 
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                        }}>
                          {task.title || 'Untitled Task'}
                        </Typography>
                        <Chip
                          label={task.priority || 'medium'}
                          color={getPriorityColor(task.priority)}
                          size="small"
                        />
                      </Box>

                      <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{ 
                          mb: 2,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          minHeight: '60px'
                        }}
                      >
                        {task.description || 'No description available'}
                      </Typography>

                      <Box sx={{ mb: 2 }}>
                        <Chip
                          label={task.status || 'todo'}
                          color={getStatusColor(task.status)}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                        {task.assignee && (
                          <Chip
                            label={`Assigned: ${task.assignee}`}
                            color="default"
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>

                      <Divider sx={{ my: 2 }} />

                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Schedule sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              {formatDuration(task.estimated_hours)}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Person sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              {task.assignee || 'Unassigned'}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Flag sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              Due: {formatDate(task.end_time)}
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </CardContent>

                    <CardActions>
                      <Button size="small" color="primary">
                        View Details
                      </Button>
                      <Button size="small" color="secondary">
                        Edit
                      </Button>
                    </CardActions>
                  </Card>
                ))}
              </Box>
              
              {/* Load More Button and Pagination Controls */}
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 4, mb: 2 }}>
                {loadingMore && (
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                )}
                
                {hasMore && !loading && (
                  <Button
                    variant="outlined"
                    onClick={loadMoreTasks}
                    disabled={loadingMore}
                    sx={{ mr: 2 }}
                  >
                    {loadingMore ? 'Loading...' : `Load More Tasks (${PAGE_SIZE} more)`}
                  </Button>
                )}
                
                {!hasMore && tasks.length > 0 && (
                  <Typography variant="body2" color="text.secondary">
                    All available tasks loaded ({tasks.length} total)
                  </Typography>
                )}
              </Box>
              </>
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
             <></>
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