import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const APIContext = createContext()

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const useAPI = () => {
  const context = useContext(APIContext)
  if (!context) {
    throw new Error('useAPI must be used within an APIProvider')
  }
  return context
}

export const APIProvider = ({ children }) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Tasks API
  const taskAPI = {
    getAll: async (filters = {}) => {
      setLoading(true)
      try {
        const params = new URLSearchParams(filters)
        const response = await apiClient.get(`/api/tasks?${params}`)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch tasks')
        throw err
      } finally {
        setLoading(false)
      }
    },

    getById: async (id) => {
      setLoading(true)
      try {
        const response = await apiClient.get(`/api/tasks/${id}`)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch task')
        throw err
      } finally {
        setLoading(false)
      }
    },

    create: async (taskData) => {
      setLoading(true)
      try {
        const response = await apiClient.post('/api/tasks', taskData)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to create task')
        throw err
      } finally {
        setLoading(false)
      }
    },

    update: async (id, taskData) => {
      setLoading(true)
      try {
        const response = await apiClient.put(`/api/tasks/${id}`, taskData)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to update task')
        throw err
      } finally {
        setLoading(false)
      }
    },

    updateStatus: async (id, status) => {
      setLoading(true)
      try {
        const response = await apiClient.patch(`/api/tasks/${id}/status`, { status })
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to update task status')
        throw err
      } finally {
        setLoading(false)
      }
    },

    delete: async (id) => {
      setLoading(true)
      try {
        await apiClient.delete(`/api/tasks/${id}`)
        setError(null)
        return true
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete task')
        throw err
      } finally {
        setLoading(false)
      }
    },

    addComment: async (id, commentData) => {
      setLoading(true)
      try {
        const response = await apiClient.post(`/api/tasks/${id}/comments`, commentData)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to add comment')
        throw err
      } finally {
        setLoading(false)
      }
    },

    getComments: async (id) => {
      setLoading(true)
      try {
        const response = await apiClient.get(`/api/tasks/${id}/comments`)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch comments')
        throw err
      } finally {
        setLoading(false)
      }
    },
  }

  // Projects API
  const projectAPI = {
    getAll: async () => {
      setLoading(true)
      try {
        const response = await apiClient.get('/api/projects')
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch projects')
        throw err
      } finally {
        setLoading(false)
      }
    },

    getById: async (id) => {
      setLoading(true)
      try {
        const response = await apiClient.get(`/api/projects/${id}`)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch project')
        throw err
      } finally {
        setLoading(false)
      }
    },

    create: async (projectData) => {
      setLoading(true)
      try {
        const response = await apiClient.post('/api/projects', projectData)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to create project')
        throw err
      } finally {
        setLoading(false)
      }
    },

    update: async (id, projectData) => {
      setLoading(true)
      try {
        const response = await apiClient.put(`/api/projects/${id}`, projectData)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to update project')
        throw err
      } finally {
        setLoading(false)
      }
    },

    delete: async (id) => {
      setLoading(true)
      try {
        await apiClient.delete(`/api/projects/${id}`)
        setError(null)
        return true
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to delete project')
        throw err
      } finally {
        setLoading(false)
      }
    },

    getStats: async (id) => {
      setLoading(true)
      try {
        const response = await apiClient.get(`/api/stats/projects/${id}`)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch project stats')
        throw err
      } finally {
        setLoading(false)
      }
    },
  }

  // AI API
  const aiAPI = {
    analyze: async (prompt) => {
      setLoading(true)
      try {
        const response = await apiClient.post('/ai/analyze', { prompt })
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to analyze workspace')
        throw err
      } finally {
        setLoading(false)
      }
    },

    chat: async (message) => {
      setLoading(true)
      try {
        const response = await apiClient.post('/ai/chat', { message })
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to send chat message')
        throw err
      } finally {
        setLoading(false)
      }
    },

    getSuggestions: async () => {
      setLoading(true)
      try {
        const response = await apiClient.get('/ai/suggestions')
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to get AI suggestions')
        throw err
      } finally {
        setLoading(false)
      }
    },

    getPendingActions: async () => {
      setLoading(true)
      try {
        const response = await apiClient.get('/ai/actions')
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to get pending actions')
        throw err
      } finally {
        setLoading(false)
      }
    },

    executeAction: async (actionId) => {
      setLoading(true)
      try {
        const response = await apiClient.post(`/ai/actions/${actionId}/execute`)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to execute action')
        throw err
      } finally {
        setLoading(false)
      }
    },
  }

  // Statistics API
  const statsAPI = {
    getOverview: async () => {
      setLoading(true)
      try {
        const response = await apiClient.get('/api/stats/overview')
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch overview stats')
        throw err
      } finally {
        setLoading(false)
      }
    },
  }

  // Integrations API
  const integrationsAPI = {
    getHistory: async (filters = {}) => {
      setLoading(true)
      try {
        const params = new URLSearchParams(filters)
        const response = await apiClient.get(`/integrations/history?${params}`)
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch integration history')
        throw err
      } finally {
        setLoading(false)
      }
    },

    sendWhatsApp: async (to, message) => {
      setLoading(true)
      try {
        const response = await apiClient.post('/integrations/whatsapp/send', { to, message })
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to send WhatsApp message')
        throw err
      } finally {
        setLoading(false)
      }
    },

    sendTelegram: async (chatId, message) => {
      setLoading(true)
      try {
        const response = await apiClient.post('/integrations/telegram/send', { 
          chat_id: chatId, 
          message 
        })
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to send Telegram message')
        throw err
      } finally {
        setLoading(false)
      }
    },

    sendEmail: async (to, subject, body) => {
      setLoading(true)
      try {
        const response = await apiClient.post('/integrations/email/send', { to, subject, body })
        setError(null)
        return response.data
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to send email')
        throw err
      } finally {
        setLoading(false)
      }
    },
  }

  const value = {
    loading,
    error,
    setError,
    taskAPI,
    projectAPI,
    aiAPI,
    statsAPI,
    integrationsAPI,
  }

  return <APIContext.Provider value={value}>{children}</APIContext.Provider>
}