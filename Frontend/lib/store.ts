import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Candidate, Recruiter, Interview } from '@/types'

// Auth Store
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
    },
  ),
)

// UI Store
interface UiState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  toggleTheme: () => void
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'dark',
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
    }),
    {
      name: 'ui-storage',
    },
  ),
)

// Candidate Store
interface CandidateState {
  profile: Candidate | null
  isLoading: boolean
  error: string | null
  setProfile: (profile: Candidate | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useCandidateStore = create<CandidateState>((set) => ({
  profile: null,
  isLoading: false,
  error: null,
  setProfile: (profile) => set({ profile }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))

// Recruiter Store
interface RecruiterState {
  profile: Recruiter | null
  isLoading: boolean
  error: string | null
  setProfile: (profile: Recruiter | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useRecruiterStore = create<RecruiterState>((set) => ({
  profile: null,
  isLoading: false,
  error: null,
  setProfile: (profile) => set({ profile }),
  setLoading: (loading: boolean) => set({ isLoading }),
  setError: (error) => set({ error }),
}))

// Interview Store
interface InterviewState {
  currentInterview: Interview | null
  isLive: boolean
  transcript: Array<{ speaker: string; text: string; timestamp: Date }> | null
  setCurrentInterview: (interview: Interview | null) => void
  setIsLive: (isLive: boolean) => void
  setTranscript: (transcript: Array<{ speaker: string; text: string; timestamp: Date }> | null) => void
  addTranscript: (speaker: string, text: string) => void
}

export const useInterviewStore = create<InterviewState>((set) => ({
  currentInterview: null,
  isLive: false,
  transcript: null,
  setCurrentInterview: (currentInterview) => set({ currentInterview }),
  setIsLive: (isLive) => set({ isLive }),
  setTranscript: (transcript) => set({ transcript }),
  addTranscript: (speaker, text) =>
    set((state) => ({
      transcript: [...(state.transcript || []), { speaker, text, timestamp: new Date() }],
    })),
}))

// Notification Store
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

interface NotificationState {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          ...notification,
          id: Date.now().toString(),
        },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}))
