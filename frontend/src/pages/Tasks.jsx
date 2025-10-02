import React, { useState, useEffect } from 'react'
import {
  Container,
  Typography,
  Button,
  Box,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  IconButton,
  Menu,
  MenuItem as MenuItemComponent,
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
} from '@mui/material'
import {
  Add,
  MoreVert,
  Edit,
  Delete,
  Comment,
  Person,
  Schedule,
  Flag,
  ExpandLess,
  ExpandMore,
  CheckCircle,
  PlayArrow,
  Pause,
  Block,
  Psychology,
  FilterList,
} from '@mui/icons-material'
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { useAPI } from '../context/APIContext'
import SemanticSearch from '../components/SemanticSearch'

const Tasks = () => {
  const { taskAPI, projectAPI, loading, error, setError } = useAPI()
  const [tasks, setTasks] = useState([])
  const [projects, setProjects] = useState([])
  const [openDialog, setOpenDialog] = useState(false)
  const [openComments, setOpenComments] = useState({})
  const [editingTask, setEditingTask] = useState(null)
  const [anchorEl, setAnchorEl] = useState(null)
  const [selectedTask, setSelectedTask] = useState(null)
  const [comments, setComments] = useState({})
  const [newComment, setNewComment] = useState('')
  const [currentTab, setCurrentTab] = useState(0) // 0 = Traditional View, 1 = Semantic Search
  const [filters, setFilters] = useState({
    project_id: '',
    status: '',
    assignee: '',
    search: '',
  })
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    project_id: '',
    assignee: '',
    start_time: null,
    end_time: null,
    estimated_hours: '',
    actual_hours: '',
  })

  const statusOptions = [
    { value: 'todo', label: 'To Do', icon: <Schedule />, color: 'default' },
    { value: 'in_progress', label: 'In Progress', icon: <PlayArrow />, color: 'primary' },
    { value: 'review', label: 'Review', icon: <Pause />, color: 'warning' },
    { value: 'done', label: 'Done', icon: <CheckCircle />, color: 'success' },
    { value: 'blocked', label: 'Blocked', icon: <Block />, color: 'error' },
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

  const handleSubmit = async () => {
    try {
      const taskData = {
        ...formData,
        start_time: formData.start_time ? formData.start_time.toISOString() : null,
        end_time: formData.end_time ? formData.end_time.toISOString() : null,
        estimated_hours: formData.estimated_hours ? parseFloat(formData.estimated_hours) : null,
        actual_hours: formData.actual_hours ? parseFloat(formData.actual_hours) : null,
      }

      if (editingTask) {
        await taskAPI.update(editingTask.id, taskData)
      } else {
        await taskAPI.create(taskData)
      }

      setOpenDialog(false)
      setEditingTask(null)
      resetForm()
      await loadTasks()
    } catch (err) {
      console.error('Failed to save task:', err)
    }
  }

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await taskAPI.updateStatus(taskId, newStatus)
      await loadTasks()
    } catch (err) {
      console.error('Failed to update task status:', err)
    }
  }

  const handleDelete = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await taskAPI.delete(taskId)
        await loadTasks()
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }
  }

  const handleAddComment = async (taskId) => {
    if (!newComment.trim()) return

    try {
      await taskAPI.addComment(taskId, {
        content: newComment,
        author: 'User', // In a real app, get from auth context
      })
      setNewComment('')
      await loadComments(taskId)
    } catch (err) {
      console.error('Failed to add comment:', err)
    }
  }

  const toggleComments = async (taskId) => {
    const isOpen = openComments[taskId]
    setOpenComments(prev => ({ ...prev, [taskId]: !isOpen }))
    
    if (!isOpen && !comments[taskId]) {
      await loadComments(taskId)
    }
  }

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      status: 'todo',
      priority: 'medium',
      project_id: '',
      assignee: '',
      start_time: null,
      end_time: null,
      estimated_hours: '',
      actual_hours: '',
    })
  }

  const openCreateDialog = () => {
    resetForm()
    setEditingTask(null)
    setOpenDialog(true)
  }

  const openEditDialog = (task) => {
    setFormData({
      title: task.title,
      description: task.description || '',
      status: task.status,
      priority: task.priority,
      project_id: task.project_id || '',
      assignee: task.assignee || '',
      start_time: task.start_time ? new Date(task.start_time) : null,
      end_time: task.end_time ? new Date(task.end_time) : null,
      estimated_hours: task.estimated_hours?.toString() || '',
      actual_hours: task.actual_hours?.toString() || '',
    })
    setEditingTask(task)
    setOpenDialog(true)
  }

  const handleMenuOpen = (event, task) => {
    setAnchorEl(event.currentTarget)
    setSelectedTask(task)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedTask(null)
  }

  const getStatusInfo = (status) => {
    return statusOptions.find(opt => opt.value === status) || statusOptions[0]
  }

  const getPriorityInfo = (priority) => {
    return priorityOptions.find(opt => opt.value === priority) || priorityOptions[1]
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString()
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
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">Tasks</Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={openCreateDialog}
          >
            New Task
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Tabs for Traditional vs Semantic Search */}
        <Paper sx={{ mb: 3 }}>
          <Tabs 
            value={currentTab} 
            onChange={(e, newValue) => setCurrentTab(newValue)}
            indicatorColor="primary"
            textColor="primary"
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
          </Tabs>
        </Paper>

        {/* Tab Content */}
        {currentTab === 0 && (
          <>
            {/* Filters */}
            <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Filters</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Project</InputLabel>
                  <Select
                    value={filters.project_id}
                    label="Project"
                    onChange={(e) => setFilters({ ...filters, project_id: e.target.value })}
                  >
                    <MenuItem value="">All Projects</MenuItem>
                    {projects.map((project) => (
                      <MenuItem key={project.id} value={project.id}>
                        {project.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
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
                  fullWidth
                  size="small"
                  label="Assignee"
                  value={filters.assignee}
                  onChange={(e) => setFilters({ ...filters, assignee: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  size="small"
                  label="Search"
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Tasks Grid */}
        <Grid container spacing={3}>
          {tasks.map((task) => {
            const statusInfo = getStatusInfo(task.status)
            const priorityInfo = getPriorityInfo(task.priority)
            
            return (
              <Grid item xs={12} key={task.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" gutterBottom>
                          {task.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {task.description || 'No description'}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                          <Chip
                            icon={statusInfo.icon}
                            label={statusInfo.label}
                            color={statusInfo.color}
                            size="small"
                          />
                          <Chip
                            icon={<Flag />}
                            label={priorityInfo.label}
                            color={priorityInfo.color}
                            variant="outlined"
                            size="small"
                          />
                          {task.assignee && (
                            <Chip
                              icon={<Person />}
                              label={task.assignee}
                              variant="outlined"
                              size="small"
                            />
                          )}
                          {task.project_name && (
                            <Chip
                              label={task.project_name}
                              variant="outlined"
                              size="small"
                            />
                          )}
                        </Box>

                        <Grid container spacing={2}>
                          <Grid item xs={12} sm={6} md={3}>
                            <Typography variant="caption" color="text.secondary">
                              Start: {formatDate(task.start_time)}
                            </Typography>
                          </Grid>
                          <Grid item xs={12} sm={6} md={3}>
                            <Typography variant="caption" color="text.secondary">
                              End: {formatDate(task.end_time)}
                            </Typography>
                          </Grid>
                          {task.estimated_hours && (
                            <Grid item xs={12} sm={6} md={3}>
                              <Typography variant="caption" color="text.secondary">
                                Estimated: {task.estimated_hours}h
                              </Typography>
                            </Grid>
                          )}
                          {task.actual_hours && (
                            <Grid item xs={12} sm={6} md={3}>
                              <Typography variant="caption" color="text.secondary">
                                Actual: {task.actual_hours}h
                              </Typography>
                            </Grid>
                          )}
                        </Grid>
                      </Box>
                      
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, task)}
                      >
                        <MoreVert />
                      </IconButton>
                    </Box>

                    {/* Comments Section */}
                    <Box sx={{ mt: 2 }}>
                      <Button
                        startIcon={<Comment />}
                        onClick={() => toggleComments(task.id)}
                        endIcon={openComments[task.id] ? <ExpandLess /> : <ExpandMore />}
                        size="small"
                      >
                        Comments ({task.comment_count || 0})
                      </Button>
                      
                      <Collapse in={openComments[task.id]}>
                        <Box sx={{ mt: 2 }}>
                          <Divider sx={{ mb: 2 }} />
                          
                          {/* Comments List */}
                          {comments[task.id] && (
                            <List dense>
                              {comments[task.id].map((comment) => (
                                <ListItem key={comment.id}>
                                  <ListItemIcon>
                                    <Person />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={comment.content}
                                    secondary={`${comment.author} - ${formatDate(comment.created_at)}`}
                                  />
                                </ListItem>
                              ))}
                            </List>
                          )}
                          
                          {/* Add Comment */}
                          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                            <TextField
                              fullWidth
                              size="small"
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
                              variant="contained"
                              size="small"
                              onClick={() => handleAddComment(task.id)}
                            >
                              Add
                            </Button>
                          </Box>
                        </Box>
                      </Collapse>
                    </Box>
                  </CardContent>

                  <CardActions>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <Select
                        value={task.status}
                        onChange={(e) => handleStatusChange(task.id, e.target.value)}
                        displayEmpty
                      >
                        {statusOptions.map((status) => (
                          <MenuItem key={status.value} value={status.value}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {status.icon}
                              {status.label}
                            </Box>
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </CardActions>
                </Card>
              </Grid>
            )
          })}
        </Grid>
          </>
        )}

        {/* Semantic Search Tab */}
        {currentTab === 1 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <SemanticSearch 
                onTaskSelect={(task) => {
                  // When a task is selected from semantic search, show it in detail
                  setSelectedTask(task)
                  setAnchorEl(null) // This will trigger the task detail view
                }} 
                maxHeight="calc(100vh - 300px)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              {selectedTask ? (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Selected Task Details
                    </Typography>
                    <Typography variant="h5" gutterBottom>
                      {selectedTask.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary" paragraph>
                      {selectedTask.description || 'No description available'}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                      <Chip
                        label={selectedTask.status?.replace('_', ' ') || 'Unknown'}
                        color={getStatusInfo(selectedTask.status)?.color || 'default'}
                      />
                      <Chip
                        label={selectedTask.priority || 'Medium'}
                        color={getPriorityInfo(selectedTask.priority)?.color || 'default'}
                        variant="outlined"
                      />
                      {selectedTask.assignee && (
                        <Chip
                          icon={<Person />}
                          label={selectedTask.assignee}
                          variant="outlined"
                        />
                      )}
                      {selectedTask.project_name && (
                        <Chip
                          label={selectedTask.project_name}
                          variant="outlined"
                          color="secondary"
                        />
                      )}
                    </Box>
                    <Box sx={{ mt: 2 }}>
                      <Button
                        variant="contained"
                        startIcon={<Edit />}
                        onClick={() => {
                          setEditingTask(selectedTask)
                          setFormData({
                            title: selectedTask.title || '',
                            description: selectedTask.description || '',
                            status: selectedTask.status || 'todo',
                            priority: selectedTask.priority || 'medium',
                            project_id: selectedTask.project_id || '',
                            assignee: selectedTask.assignee || '',
                            start_time: selectedTask.start_time ? new Date(selectedTask.start_time) : null,
                            end_time: selectedTask.end_time ? new Date(selectedTask.end_time) : null,
                            estimated_hours: selectedTask.estimated_hours || '',
                            actual_hours: selectedTask.actual_hours || '',
                          })
                          setOpenDialog(true)
                        }}
                        sx={{ mr: 1 }}
                      >
                        Edit Task
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={() => setSelectedTask(null)}
                      >
                        Clear Selection
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent sx={{ textAlign: 'center', py: 8 }}>
                    <Psychology sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      Select a task from semantic search
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Use the semantic search panel to find tasks with natural language,
                      then click on a result to see details here.
                    </Typography>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        )}

        {/* Task Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingTask ? 'Edit Task' : 'Create New Task'}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  autoFocus
                  label="Task Title"
                  fullWidth
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  label="Description"
                  fullWidth
                  multiline
                  rows={4}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={formData.status}
                    label="Status"
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  >
                    {statusOptions.map((status) => (
                      <MenuItem key={status.value} value={status.value}>
                        {status.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={formData.priority}
                    label="Priority"
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  >
                    {priorityOptions.map((priority) => (
                      <MenuItem key={priority.value} value={priority.value}>
                        {priority.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Project</InputLabel>
                  <Select
                    value={formData.project_id}
                    label="Project"
                    onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  >
                    <MenuItem value="">No Project</MenuItem>
                    {projects.map((project) => (
                      <MenuItem key={project.id} value={project.id}>
                        {project.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Assignee"
                  fullWidth
                  value={formData.assignee}
                  onChange={(e) => setFormData({ ...formData, assignee: e.target.value })}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <DateTimePicker
                  label="Start Time"
                  value={formData.start_time}
                  onChange={(date) => setFormData({ ...formData, start_time: date })}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <DateTimePicker
                  label="End Time"
                  value={formData.end_time}
                  onChange={(date) => setFormData({ ...formData, end_time: date })}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Estimated Hours"
                  type="number"
                  fullWidth
                  value={formData.estimated_hours}
                  onChange={(e) => setFormData({ ...formData, estimated_hours: e.target.value })}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Actual Hours"
                  type="number"
                  fullWidth
                  value={formData.actual_hours}
                  onChange={(e) => setFormData({ ...formData, actual_hours: e.target.value })}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
            <Button onClick={handleSubmit} variant="contained">
              {editingTask ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Context Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItemComponent
            onClick={() => {
              openEditDialog(selectedTask)
              handleMenuClose()
            }}
          >
            <Edit sx={{ mr: 1 }} /> Edit
          </MenuItemComponent>
          <MenuItemComponent
            onClick={() => {
              handleDelete(selectedTask.id)
              handleMenuClose()
            }}
          >
            <Delete sx={{ mr: 1 }} /> Delete
          </MenuItemComponent>
        </Menu>
      </Container>
    </LocalizationProvider>
  )
}

export default Tasks