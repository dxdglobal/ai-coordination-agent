import React, { useState, useEffect, useRef, useContext } from 'react'
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Paper,
  Tabs,
  Tab,
  TextField,
  IconButton,
  Avatar,
  InputAdornment,
  CircularProgress,
  Stack,
  Divider,
} from '@mui/material'
import {
  FolderOpen,
  Send,
  SmartToy,
  Chat,
  ViewList,
  Business,
  Schedule,
  Assignment,
  TrendingUp,
  AccessTime,
  CheckCircle,
  Warning,
  Search,
} from '@mui/icons-material'
import axios from 'axios'
import { AuthContext } from '../context/AuthContext'
import ProjectSearch from '../components/ProjectSearch'

const Projects = () => {
  const { user } = useContext(AuthContext)
  const [allProjects, setAllProjects] = useState([]) // Store all projects from API
  const [projects, setProjects] = useState([]) // Filtered projects for display
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [currentTab, setCurrentTab] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [isSearchMode, setIsSearchMode] = useState(false)
  const [stats, setStats] = useState(null)
  const [currentOffset, setCurrentOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [currentStatusFilter, setCurrentStatusFilter] = useState(null)
  const [currentPriorityFilter, setCurrentPriorityFilter] = useState(null)
  const [nameSearchQuery, setNameSearchQuery] = useState('')
  const ITEMS_PER_PAGE = 1000 // Increased to show all projects
  
  // Chat system state
  const [chatMessages, setChatMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const chatEndRef = useRef(null)

  const API_BASE_URL = 'http://127.0.0.1:5001'

  useEffect(() => {
    loadAllProjects()
    loadProjectStats()
  }, [])

  // Client-side filtering function
  const applyFilters = () => {
    let filtered = [...allProjects]

    // Apply status filter
    if (currentStatusFilter) {
      filtered = filtered.filter(project => project.status_id === currentStatusFilter)
    }

    // Apply priority filter
    if (currentPriorityFilter) {
      filtered = filtered.filter(project => 
        project.priority && project.priority.toLowerCase() === currentPriorityFilter.toLowerCase()
      )
    }

    // Apply name search
    if (nameSearchQuery.trim()) {
      filtered = filtered.filter(project =>
        project.name && project.name.toLowerCase().includes(nameSearchQuery.toLowerCase())
      )
    }

    setProjects(filtered)
    setIsSearchMode(currentStatusFilter !== null || currentPriorityFilter !== null || nameSearchQuery.trim() !== '')
  }

  // Apply filters whenever filter states change
  useEffect(() => {
    if (allProjects.length > 0) {
      applyFilters()
    }
  }, [allProjects, currentStatusFilter, currentPriorityFilter, nameSearchQuery])

  const loadProjects = async () => {
    try {
      setLoading(true)
      setError('')
      
      const response = await axios.get(`${API_BASE_URL}/api/projects/`)
      
      if (response.data.success) {
        setProjects(response.data.projects)
      } else {
        setError('Failed to load projects')
      }
    } catch (err) {
      console.error('Failed to load projects:', err)
      setError(err.response?.data?.error || 'Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  const loadProjectStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/projects/stats`)
      
      if (response.data.success) {
        setStats(response.data.stats)
      }
    } catch (err) {
      console.error('Failed to load project stats:', err)
    }
  }

  const handleAdvancedSearch = async (searchParams, append = false) => {
    try {
      setLoading(!append)
      if (append) setLoadingMore(true)
      setError('')
      setIsSearchMode(true)
      
      const offset = append ? currentOffset : 0
      
      // Always use search endpoint for consistency
      const response = await axios.post(`${API_BASE_URL}/api/projects/search`, {
        ...searchParams,
        limit: ITEMS_PER_PAGE,
        offset: offset,
        sort_by: searchParams.sort_by || 'id',
        sort_order: searchParams.sort_order || 'DESC'
      })
      
      if (response.data.success) {
        const newProjects = response.data.projects
        if (append) {
          setProjects(prev => [...prev, ...newProjects])
        } else {
          setProjects(newProjects)
          setCurrentOffset(0)
        }
        
        // Check if there are more projects to load
        setHasMore(newProjects.length === ITEMS_PER_PAGE)
        if (append) {
          setCurrentOffset(offset + newProjects.length)
        } else {
          setCurrentOffset(newProjects.length)
        }
        
        setSearchResults(response.data)
      } else {
        setError('Failed to search projects')
      }
    } catch (err) {
      console.error('Failed to search projects:', err)
      setError(err.response?.data?.error || 'Failed to search projects')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  // Quick status filter function (client-side)
  const filterByStatus = (statusId) => {
    setCurrentStatusFilter(statusId)
  }

  // Quick priority filter function (client-side)
  const filterByPriority = (priority) => {
    setCurrentPriorityFilter(priority)
  }

  // Search by name function (client-side)
  const searchByName = (searchTerm) => {
    setNameSearchQuery(searchTerm)
  }

  const loadAllProjects = async (append = false) => {
    try {
      setLoading(!append)
      if (append) setLoadingMore(true)
      setError('')
      
      const offset = append ? currentOffset : 0
      
      // Use search endpoint with no filters to get all projects
      const response = await axios.post(`${API_BASE_URL}/api/projects/search`, {
        limit: ITEMS_PER_PAGE,
        offset: offset,
        sort_by: 'id',
        sort_order: 'DESC'
      })
      
      if (response.data.success) {
        const newProjects = response.data.projects
        if (append) {
          const updatedProjects = [...allProjects, ...newProjects]
          setAllProjects(updatedProjects)
          setProjects(updatedProjects) // Show all by default
        } else {
          setAllProjects(newProjects)
          setProjects(newProjects) // Show all by default
          setCurrentOffset(0)
        }
        
        // Since we increased the limit to 1000, we should get all projects in one go
        setHasMore(newProjects.length === ITEMS_PER_PAGE && newProjects.length >= 294)
        if (append) {
          setCurrentOffset(offset + newProjects.length)
        } else {
          setCurrentOffset(newProjects.length)
        }
        
        setSearchResults(response.data)
      } else {
        setError('Failed to load projects')
      }
    } catch (err) {
      console.error('Failed to load projects:', err)
      setError(err.response?.data?.error || 'Failed to connect to server')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const handleClearSearch = () => {
    setIsSearchMode(false)
    setSearchResults(null)
    setSearchQuery('')
    setCurrentOffset(0)
    setHasMore(true)
    setCurrentStatusFilter(null)
    setCurrentPriorityFilter(null)
    setNameSearchQuery('')
    setProjects([...allProjects]) // Reset to show all projects
  }

  const showAllProjects = () => {
    setCurrentStatusFilter(null)
    setCurrentPriorityFilter(null) 
    setNameSearchQuery('')
    setIsSearchMode(false)
    setProjects([...allProjects]) // Show all projects
  }

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'finished': return 'success'
      case 'in progress': return 'primary'
      case 'on hold': return 'warning'
      case 'cancelled': return 'error'
      case 'not started': return 'default'
      default: return 'default'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'error'
      case 'medium': return 'warning'
      case 'low': return 'success'
      default: return 'default'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString()
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
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
            projects: projects,
            currentPage: 'projects'
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
    <Box sx={{ width: '100%', pb: 4,mb: 40 }}>
      <Container maxWidth="lg" sx={{ mt: 5, mb: 5, minHeight: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Projects Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage and monitor all your projects from the CRM database
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
            icon={<ViewList />} 
            label="Project List" 
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
          {/* Advanced Search Component */}
          <ProjectSearch 
            onSearch={handleAdvancedSearch}
            onClear={handleClearSearch}
            searchResults={searchResults}
          />

          {/* Quick Status Filters */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Status Filters
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              <Chip
                label="All Projects"
                onClick={() => showAllProjects()}
                variant={currentStatusFilter === null ? "filled" : "outlined"}
                color="primary"
              />
              <Chip
                label="Not Started"
                onClick={() => filterByStatus(1)}
                variant={currentStatusFilter === 1 ? "filled" : "outlined"}
                color="default"
              />
              <Chip
                label="In Progress"
                onClick={() => filterByStatus(2)}
                variant={currentStatusFilter === 2 ? "filled" : "outlined"}
                color="primary"
              />
              <Chip
                label="On Hold"
                onClick={() => filterByStatus(3)}
                variant={currentStatusFilter === 3 ? "filled" : "outlined"}
                color="warning"
              />
              <Chip
                label="Cancelled"
                onClick={() => filterByStatus(4)}
                variant={currentStatusFilter === 4 ? "filled" : "outlined"}
                color="error"
              />
              <Chip
                label="Finished"
                onClick={() => filterByStatus(5)}
                variant={currentStatusFilter === 5 ? "filled" : "outlined"}
                color="success"
              />
            </Stack>
          </Paper>

          {/* Priority Filters */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Priority Filters
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              <Chip
                label="All Priorities"
                onClick={() => setCurrentPriorityFilter(null)}
                variant={currentPriorityFilter === null ? "filled" : "outlined"}
                color="primary"
              />
              <Chip
                label="High Priority"
                onClick={() => filterByPriority('High')}
                variant={currentPriorityFilter === 'High' ? "filled" : "outlined"}
                color="error"
              />
              <Chip
                label="Medium Priority"
                onClick={() => filterByPriority('Medium')}
                variant={currentPriorityFilter === 'Medium' ? "filled" : "outlined"}
                color="warning"
              />
              <Chip
                label="Low Priority"
                onClick={() => filterByPriority('Low')}
                variant={currentPriorityFilter === 'Low' ? "filled" : "outlined"}
                color="success"
              />
            </Stack>
          </Paper>

          {/* Search by Name */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Search by Project Name
            </Typography>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Enter project name to search..."
              value={nameSearchQuery}
              onChange={(e) => setNameSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
                endAdornment: nameSearchQuery && (
                  <InputAdornment position="end">
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => setNameSearchQuery('')}
                    >
                      Clear
                    </Button>
                  </InputAdornment>
                )
              }}
            />
          </Paper>

          {/* Filter Status Display */}
          {isSearchMode && (
            <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
              <Typography variant="body2" color="textSecondary">
                <strong>Showing {projects.length} of {allProjects.length} projects</strong>
                {currentStatusFilter && (
                  <span> • Status: {
                    currentStatusFilter === 1 ? 'Not Started' :
                    currentStatusFilter === 2 ? 'In Progress' :
                    currentStatusFilter === 3 ? 'On Hold' :
                    currentStatusFilter === 4 ? 'Cancelled' :
                    currentStatusFilter === 5 ? 'Finished' : ''
                  }</span>
                )}
                {currentPriorityFilter && (
                  <span> • Priority: {currentPriorityFilter}</span>
                )}
                {nameSearchQuery && (
                  <span> • Name contains: "{nameSearchQuery}"</span>
                )}
                <Button
                  size="small"
                  onClick={handleClearSearch}
                  sx={{ ml: 2 }}
                  variant="text"
                >
                  Clear All Filters
                </Button>
              </Typography>
            </Paper>
          )}

          {/* Statistics Cards */}
          {stats && !isSearchMode && (
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Business sx={{ color: 'primary.main', mr: 2 }} />
                      <Box>
                        <Typography variant="h4">{stats.total_projects}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Projects
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
                      <TrendingUp sx={{ color: 'success.main', mr: 2 }} />
                      <Box>
                        <Typography variant="h4">{stats.active_projects}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Active Projects
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
                      <CheckCircle sx={{ color: 'success.main', mr: 2 }} />
                      <Box>
                        <Typography variant="h4">{stats.completed_projects}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Completed
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
                      <Warning sx={{ color: 'warning.main', mr: 2 }} />
                      <Box>
                        <Typography variant="h4">{stats.overdue_projects}</Typography>
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
          ) : projects.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <FolderOpen sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {isSearchMode ? 'No projects found matching your filters' : 'No projects found'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {isSearchMode ? (
                  <>
                    Try adjusting your search terms or filters
                    <Button
                      variant="outlined"
                      onClick={handleClearSearch}
                      sx={{ mt: 2, display: 'block', mx: 'auto' }}
                    >
                      Clear All Filters
                    </Button>
                  </>
                ) : 'Projects will appear here when they are available'}
              </Typography>
            </Box>
          ) : (
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
              {projects.map((project) => (
                <Card 
                  key={project.id}
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
                          {project.name}
                        </Typography>
                        <Chip
                          label={project.priority}
                          color={getPriorityColor(project.priority)}
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
                        {project.description || 'No description available'}
                      </Typography>

                      <Box sx={{ mb: 2 }}>
                        <Chip
                          label={project.status}
                          color={getStatusColor(project.status)}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                        {project.is_overdue && (
                          <Chip
                            label="OVERDUE"
                            color="error"
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>

                      <Stack spacing={1}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">
                            Progress
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {project.completion_percentage}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={project.completion_percentage} 
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Stack>

                      <Divider sx={{ my: 2 }} />

                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Assignment sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              {project.total_tasks} tasks
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <CheckCircle sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              {project.completed_tasks} done
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Schedule sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              Start: {formatDate(project.start_date)}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <AccessTime sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary">
                              Due: {formatDate(project.deadline)}
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>

                      {(project.project_cost > 0 || project.hourly_rate > 0) && (
                        <>
                          <Divider sx={{ my: 2 }} />
                          <Grid container spacing={1}>
                            {project.project_cost > 0 && (
                              <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                  Budget: {formatCurrency(project.project_cost)}
                                </Typography>
                              </Grid>
                            )}
                            {project.hourly_rate > 0 && (
                              <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                  Rate: {formatCurrency(project.hourly_rate)}/hr
                                </Typography>
                              </Grid>
                            )}
                          </Grid>
                        </>
                      )}
                    </CardContent>

                    <CardActions>
                      <Button size="small" color="primary">
                        View Details
                      </Button>
                      <Button size="small" color="secondary">
                        Edit Tasks
                      </Button>
                    </CardActions>
                  </Card>
              ))}
            </Box>
          )}

          {/* Load More / Show All Button */}
          {hasMore && projects.length > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 4, mb: 2 }}>
              <Button
                variant="outlined"
                size="large"
                onClick={() => isSearchMode ? 
                  handleAdvancedSearch(searchResults?.search_params || {}, true) : 
                  loadAllProjects(true)
                }
                disabled={loadingMore}
                startIcon={loadingMore ? <CircularProgress size={20} /> : null}
              >
                {loadingMore ? 'Loading...' : 'Load More Projects'}
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={() => showAllProjects()}
                disabled={loadingMore}
                color="primary"
              >
                Show All Projects
              </Button>
            </Box>
          )}

          {/* No more projects message */}
          {!hasMore && projects.length > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Showing all {projects.length} {
                  currentStatusFilter === 1 ? 'Not Started' :
                  currentStatusFilter === 2 ? 'In Progress' :
                  currentStatusFilter === 3 ? 'On Hold' :
                  currentStatusFilter === 4 ? 'Cancelled' :
                  currentStatusFilter === 5 ? 'Finished' :
                  ''
                } projects{currentStatusFilter ? '' : ' (All)'}
              </Typography>
            </Box>
          )}
        </>
      )}

      {currentTab === 1 && (
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
                    Ask me anything about your projects and their status
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
                    Ask me about your projects, their status, deadlines, or anything else you need help with.
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
                  placeholder="Ask me about your projects..."
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
    </Box>
  )
}

export default Projects