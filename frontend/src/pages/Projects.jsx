import React, { useState, useEffect } from 'react'
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
} from '@mui/material'
import {
  Add,
  MoreVert,
  Edit,
  Delete,
  Visibility,
  FolderOpen,
} from '@mui/icons-material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { useAPI } from '../context/APIContext'

const Projects = () => {
  const { projectAPI, loading, error, setError } = useAPI()
  const [projects, setProjects] = useState([])
  const [openDialog, setOpenDialog] = useState(false)
  const [editingProject, setEditingProject] = useState(null)
  const [anchorEl, setAnchorEl] = useState(null)
  const [selectedProject, setSelectedProject] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'todo',
    start_date: null,
    end_date: null,
    deadline: null,
  })

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const data = await projectAPI.getAll()
      setProjects(data)
    } catch (err) {
      console.error('Failed to load projects:', err)
    }
  }

  const handleSubmit = async () => {
    try {
      const projectData = {
        ...formData,
        start_date: formData.start_date ? formData.start_date.toISOString() : null,
        end_date: formData.end_date ? formData.end_date.toISOString() : null,
        deadline: formData.deadline ? formData.deadline.toISOString() : null,
      }

      if (editingProject) {
        await projectAPI.update(editingProject.id, projectData)
      } else {
        await projectAPI.create(projectData)
      }

      setOpenDialog(false)
      setEditingProject(null)
      resetForm()
      await loadProjects()
    } catch (err) {
      console.error('Failed to save project:', err)
    }
  }

  const handleDelete = async (projectId) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        await projectAPI.delete(projectId)
        await loadProjects()
      } catch (err) {
        console.error('Failed to delete project:', err)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      status: 'todo',
      start_date: null,
      end_date: null,
      deadline: null,
    })
  }

  const openCreateDialog = () => {
    resetForm()
    setEditingProject(null)
    setOpenDialog(true)
  }

  const openEditDialog = (project) => {
    setFormData({
      name: project.name,
      description: project.description || '',
      status: project.status,
      start_date: project.start_date ? new Date(project.start_date) : null,
      end_date: project.end_date ? new Date(project.end_date) : null,
      deadline: project.deadline ? new Date(project.deadline) : null,
    })
    setEditingProject(project)
    setOpenDialog(true)
  }

  const handleMenuOpen = (event, project) => {
    setAnchorEl(event.currentTarget)
    setSelectedProject(project)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedProject(null)
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
          <Typography variant="h4">Projects</Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={openCreateDialog}
          >
            New Project
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Typography gutterBottom variant="h6" component="div">
                      {project.name}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, project)}
                    >
                      <MoreVert />
                    </IconButton>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {project.description || 'No description'}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={project.status?.replace('_', ' ')}
                      color={getStatusColor(project.status)}
                      size="small"
                    />
                  </Box>

                  <Typography variant="body2" color="text.secondary">
                    Tasks: {project.task_count || 0}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary">
                    Deadline: {formatDate(project.deadline)}
                  </Typography>
                </CardContent>

                <CardActions>
                  <Button size="small" startIcon={<Visibility />}>
                    View Details
                  </Button>
                  <Button
                    size="small"
                    startIcon={<FolderOpen />}
                    onClick={() => window.location.href = `/tasks?project_id=${project.id}`}
                  >
                    Tasks
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Project Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {editingProject ? 'Edit Project' : 'Create New Project'}
          </DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Project Name"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              sx={{ mb: 2 }}
            />

            <TextField
              margin="dense"
              label="Description"
              fullWidth
              multiline
              rows={4}
              variant="outlined"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                label="Status"
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              >
                <MenuItem value="todo">To Do</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="review">Review</MenuItem>
                <MenuItem value="done">Done</MenuItem>
                <MenuItem value="blocked">Blocked</MenuItem>
              </Select>
            </FormControl>

            <DatePicker
              label="Start Date"
              value={formData.start_date}
              onChange={(date) => setFormData({ ...formData, start_date: date })}
              renderInput={(params) => <TextField {...params} fullWidth sx={{ mb: 2 }} />}
            />

            <DatePicker
              label="End Date"
              value={formData.end_date}
              onChange={(date) => setFormData({ ...formData, end_date: date })}
              renderInput={(params) => <TextField {...params} fullWidth sx={{ mb: 2 }} />}
            />

            <DatePicker
              label="Deadline"
              value={formData.deadline}
              onChange={(date) => setFormData({ ...formData, deadline: date })}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
            <Button onClick={handleSubmit} variant="contained">
              {editingProject ? 'Update' : 'Create'}
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
              openEditDialog(selectedProject)
              handleMenuClose()
            }}
          >
            <Edit sx={{ mr: 1 }} /> Edit
          </MenuItemComponent>
          <MenuItemComponent
            onClick={() => {
              handleDelete(selectedProject.id)
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

export default Projects