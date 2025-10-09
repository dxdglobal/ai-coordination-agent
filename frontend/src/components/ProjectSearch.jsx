import React, { useState } from 'react'
import {
  Box,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  Typography,
  Paper
} from '@mui/material'
import {
  Search,
  Clear
} from '@mui/icons-material'

const ProjectSearch = ({ onSearch, onClear, searchResults }) => {
  const [searchParams, setSearchParams] = useState({
    query: '',
    status: '',
    sort_by: 'id',
    sort_order: 'DESC'
  })

  const handleInputChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setSearchParams(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSearch = () => {
    // Filter out empty values
    const cleanParams = {}
    Object.keys(searchParams).forEach(key => {
      if (searchParams[key] !== '' && searchParams[key] !== false) {
        cleanParams[key] = searchParams[key]
      }
    })
    onSearch(cleanParams)
  }

  const handleClear = () => {
    setSearchParams({
      query: '',
      status: '',
      sort_by: 'id',
      sort_order: 'DESC'
    })
    onClear()
  }

  const statusOptions = [
    { value: 1, label: 'Not Started' },
    { value: 2, label: 'In Progress' },
    { value: 3, label: 'On Hold' },
    { value: 4, label: 'Cancelled' },
    { value: 5, label: 'Finished' }
  ]

  const sortOptions = [
    { value: 'name', label: 'Name' },
    { value: 'status', label: 'Status' },
    { value: 'start_date', label: 'Start Date' },
    { value: 'deadline', label: 'Deadline' },
    { value: 'dateadded', label: 'Created Date' },
    { value: 'project_cost', label: 'Budget' },
    { value: 'total_tasks', label: 'Task Count' }
  ]

  const getActiveFiltersCount = () => {
    let count = 0
    if (searchParams.query) count++
    if (searchParams.status) count++
    if (searchParams.start_date_from || searchParams.start_date_to) count++
    if (searchParams.deadline_from || searchParams.deadline_to) count++
    if (searchParams.budget_min || searchParams.budget_max) count++
    if (searchParams.overdue_only || searchParams.active_only || searchParams.has_tasks) count++
    return count
  }

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Search />
        Advanced Project Search
        {getActiveFiltersCount() > 0 && (
          <Chip 
            label={`${getActiveFiltersCount()} filters active`} 
            size="small" 
            color="primary" 
          />
        )}
      </Typography>

      {/* Basic Search */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Search projects, clients, tasks..."
            value={searchParams.query}
            onChange={handleInputChange('query')}
            placeholder="e.g. website, marketing, John Smith"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={searchParams.status}
              onChange={handleInputChange('status')}
              label="Status"
            >
              <MenuItem value="">All Statuses</MenuItem>
              {statusOptions.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              onClick={handleSearch}
              startIcon={<Search />}
              fullWidth
            >
              Search
            </Button>
            <Button
              variant="outlined"
              onClick={handleClear}
              startIcon={<Clear />}
            >
              Clear
            </Button>
          </Box>
        </Grid>
      </Grid>

      {/* Search Results Summary */}
      {searchResults && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Found {searchResults.total_count} projects
            {searchResults.returned_count < searchResults.total_count && 
              ` (showing ${searchResults.returned_count})`
            }
            {searchResults.search_params?.query && 
              ` matching "${searchResults.search_params.query}"`
            }
          </Typography>
        </Box>
      )}
    </Paper>
  )
}

export default ProjectSearch