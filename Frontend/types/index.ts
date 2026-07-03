// User Types
export type UserRole = 'recruiter' | 'candidate' | 'admin' | 'interviewer'

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  avatar?: string
  createdAt: Date
  updatedAt: Date
}

// Recruiter Types
export interface Recruiter extends User {
  role: 'recruiter'
  company?: string
  jobsPosted?: number
  candidatesReviewed?: number
}

// Candidate Types
export interface CandidateSkill {
  name: string
  proficiency: number // 0-100
  years: number
}

export interface Candidate extends User {
  role: 'candidate'
  headline?: string
  skills: CandidateSkill[]
  experience: number
  resumeUrl?: string
  interviewsCompleted: number
}

// Job Types
export interface Job {
  id: string
  title: string
  company: string
  description: string
  requirements: string[]
  skills: CandidateSkill[]
  salary?: {
    min: number
    max: number
    currency: string
  }
  status: 'open' | 'closed' | 'draft'
  createdAt: Date
  updatedAt: Date
}

// Interview Types
export type InterviewStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
export type InterviewType = 'technical' | 'behavioral' | 'coding' | 'system_design'

export interface Interview {
  id: string
  jobId: string
  candidateId: string
  recruiterId: string
  type: InterviewType
  status: InterviewStatus
  scheduledAt: Date
  duration: number // minutes
  transcript?: string
  recording?: string
  evaluationScore?: number
  notes?: string
  createdAt: Date
  updatedAt: Date
}

// Question Types
export interface Question {
  id: string
  interviewId: string
  text: string
  type: 'open' | 'coding' | 'multiple_choice'
  difficulty: 'easy' | 'medium' | 'hard'
  timestamp: Date
  answer?: string
  score?: number
}

// Analytics Types
export interface SkillMetrics {
  name: string
  score: number
  trend: 'up' | 'down' | 'stable'
}

export interface InterviewMetrics {
  total: number
  completed: number
  averageScore: number
  topSkills: SkillMetrics[]
  timeline: Array<{
    date: Date
    count: number
  }>
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T[]
  pagination: {
    total: number
    page: number
    limit: number
    hasMore: boolean
  }
  error?: string
}
