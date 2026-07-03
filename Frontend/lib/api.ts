import axios, { AxiosError, AxiosRequestConfig } from 'axios'
import type { ApiResponse, PaginatedResponse } from '@/types'

// Configure API base URL to route through Next.js rewrite
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Handle responses
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
        window.location.href = '/auth/login'
      }
    }
    return Promise.reject(error)
  },
)

export class ApiService {
  static async get<T>(url: string, config?: AxiosRequestConfig) {
    try {
      const response = await apiClient.get<ApiResponse<T>>(url, config)
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  static async post<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    try {
      const response = await apiClient.post<ApiResponse<T>>(url, data, config)
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  static async put<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    try {
      const response = await apiClient.put<ApiResponse<T>>(url, data, config)
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  static async patch<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    try {
      const response = await apiClient.patch<ApiResponse<T>>(url, data, config)
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  static async delete<T>(url: string, config?: AxiosRequestConfig) {
    try {
      const response = await apiClient.delete<ApiResponse<T>>(url, config)
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  static async getPaginated<T>(url: string, config?: AxiosRequestConfig) {
    try {
      const response = await apiClient.get<PaginatedResponse<T>>(url, config)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  private static handleError(error: any) {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.error || error.message
      return new Error(message)
    }
    return error
  }
}

// Specific API endpoints
export const ApiEndpoints = {
  // Auth (Routes to candidate-service port 8001)
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    register: '/auth/register',
    refresh: '/auth/refresh',
    me: '/auth/me',
  },
  // Recruiter Platform (Routes to recruiter-platform port 8007)
  recruiter: {
    dashboard: (id: string) => `/recruiter/candidates/${id}/dashboard`,
    comparisons: '/recruiter/comparisons',
    search: '/recruiter/search',
  },
  // Candidate Platform (Routes to candidate-platform port 8008)
  candidates: {
    dashboard: (id: string) => `/candidates/${id}/dashboard`,
    skills: (id: string) => `/candidates/${id}/skills`,
  },
  // Interviews (Routes to interview-engine port 8003)
  interviews: {
    list: '/interviews',
    create: '/interviews',
    get: (id: string) => `/interviews/${id}`,
    start: (id: string) => `/interviews/${id}/start`,
  }
}
