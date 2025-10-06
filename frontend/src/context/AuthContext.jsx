import React, { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext()

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  // API base URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  useEffect(() => {
    // Check if user is already logged in (token in localStorage)
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('authToken')
      if (token) {
        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        // Validate token with backend
        const response = await axios.get(`${API_BASE_URL}/auth/me`)
        
        if (response.data.success) {
          setUser(response.data.user)
          setIsAuthenticated(true)
        } else {
          // Token invalid, clear it
          localStorage.removeItem('authToken')
          delete axios.defaults.headers.common['Authorization']
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      // Clear invalid token
      localStorage.removeItem('authToken')
      delete axios.defaults.headers.common['Authorization']
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      setLoading(true)
      
      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        username,
        password
      })

      if (response.data.success) {
        const { token, user } = response.data
        
        // Store token
        localStorage.setItem('authToken', token)
        
        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        // Update state
        setUser(user)
        setIsAuthenticated(true)
        
        return { success: true, user }
      } else {
        throw new Error(response.data.message || 'Login failed')
      }
    } catch (error) {
      console.error('Login error:', error)
      
      if (error.response?.data?.message) {
        throw new Error(error.response.data.message)
      } else if (error.response?.status === 401) {
        throw new Error('Invalid username or password')
      } else if (error.response?.status >= 500) {
        throw new Error('Server error. Please try again later.')
      } else {
        throw new Error('Login failed. Please check your connection.')
      }
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      // Call logout endpoint if available
      await axios.post(`${API_BASE_URL}/auth/logout`)
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear local state regardless of API call result
      localStorage.removeItem('authToken')
      delete axios.defaults.headers.common['Authorization']
      setUser(null)
      setIsAuthenticated(false)
    }
  }

  const refreshToken = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`)
      
      if (response.data.success) {
        const { token } = response.data
        localStorage.setItem('authToken', token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        return true
      }
      return false
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout() // Force logout on refresh failure
      return false
    }
  }

  // Mock login for development (when backend is not available)
  const mockLogin = async (username, password) => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (username === 'admin' && password === 'admin123') {
          const mockUser = {
            id: 1,
            username: 'admin',
            name: 'Administrator',
            email: 'admin@aicoordination.com',
            role: 'admin',
            permissions: ['read', 'write', 'admin']
          }
          
          const mockToken = 'mock-jwt-token-' + Date.now()
          
          localStorage.setItem('authToken', mockToken)
          axios.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`
          
          setUser(mockUser)
          setIsAuthenticated(true)
          
          resolve({ success: true, user: mockUser })
        } else {
          reject(new Error('Invalid credentials'))
        }
      }, 1000) // Simulate network delay
    })
  }

  // Enhanced login that tries real API first, then falls back to mock
  const enhancedLogin = async (username, password) => {
    try {
      // Try real API first
      return await login(username, password)
    } catch (error) {
      console.warn('Real API login failed, trying mock login:', error.message)
      
      // Fall back to mock login for development
      if (process.env.NODE_ENV === 'development') {
        return await mockLogin(username, password)
      }
      
      throw error
    }
  }

  const value = {
    user,
    isAuthenticated,
    loading,
    login: enhancedLogin,
    logout,
    refreshToken,
    checkAuthStatus
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export { AuthContext }