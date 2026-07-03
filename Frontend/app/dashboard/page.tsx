'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, Users, Briefcase, TrendingUp, Calendar, MessageSquare, Activity } from 'lucide-react'
import { AppLayout } from '@/components/layout/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

interface StatCard {
  title: string
  value: string | number
  change?: string
  trend?: 'up' | 'down'
  icon: React.ReactNode
}

interface RecentActivity {
  id: string
  type: 'interview' | 'application' | 'message'
  title: string
  description: string
  timestamp: string
  status: 'completed' | 'pending' | 'in_progress'
}

const stats: StatCard[] = [
  {
    title: 'Total Candidates',
    value: '1,247',
    change: '+12%',
    trend: 'up',
    icon: <Users className="w-5 h-5" />,
  },
  {
    title: 'Active Jobs',
    value: '24',
    change: '+3',
    trend: 'up',
    icon: <Briefcase className="w-5 h-5" />,
  },
  {
    title: 'Interviews',
    value: '142',
    change: '+8%',
    trend: 'up',
    icon: <BarChart3 className="w-5 h-5" />,
  },
  {
    title: 'Pipeline Value',
    value: '$2.4M',
    change: '+18%',
    trend: 'up',
    icon: <TrendingUp className="w-5 h-5" />,
  },
]

const recentActivities: RecentActivity[] = [
  {
    id: '1',
    type: 'interview',
    title: 'Interview Scheduled',
    description: 'Sarah Anderson interviewed for Senior Engineer position',
    timestamp: '2 hours ago',
    status: 'completed',
  },
  {
    id: '2',
    type: 'application',
    title: 'New Application',
    description: 'John Smith applied for Product Manager role',
    timestamp: '4 hours ago',
    status: 'pending',
  },
  {
    id: '3',
    type: 'message',
    title: 'Message Received',
    description: 'Emily Johnson sent feedback on tech assessment',
    timestamp: '6 hours ago',
    status: 'in_progress',
  },
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-500/10 text-green-600 dark:text-green-400'
    case 'pending':
      return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
    case 'in_progress':
      return 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
    default:
      return 'bg-gray-500/10 text-gray-600 dark:text-gray-400'
  }
}

export default function DashboardPage() {
  const [dynamicStats, setDynamicStats] = useState<StatCard[]>(stats)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const { ApiService, ApiEndpoints } = await import('@/lib/api')
        // Fetch candidate dashboard data to demonstrate backend integration (port 8008 proxy)
        const data: any = await ApiService.get(ApiEndpoints.candidates.dashboard('c_123'))
        
        if (data) {
          setDynamicStats([
            {
              title: 'Upcoming Interviews',
              value: data.upcoming_interviews || 0,
              icon: <Calendar className="w-5 h-5" />,
            },
            {
              title: 'Readiness Score',
              value: `${(data.readiness_score * 100).toFixed(0)}%`,
              trend: 'up',
              icon: <Activity className="w-5 h-5" />,
            },
            {
              title: 'Recommended Topics',
              value: data.recommended_topics?.length || 0,
              icon: <Briefcase className="w-5 h-5" />,
            },
            {
              title: 'Recent Feedback',
              value: 'Available',
              icon: <MessageSquare className="w-5 h-5" />,
            }
          ])
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchDashboardData()
  }, [])

  return (
    <AppLayout>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
        {/* Page Header */}
        <motion.div variants={item} className="space-y-2">
          <h1 className="text-3xl font-bold">Welcome back!</h1>
          <p className="text-muted-foreground">
            Here&apos;s what&apos;s happening with your talent pipeline today.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={container}
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
        >
          {isLoading ? (
             <p className="text-muted-foreground p-4">Loading dynamic stats from backend...</p>
          ) : dynamicStats.map((stat) => (
            <motion.div key={stat.title} variants={item}>
              <Card className="hover:border-accent/50 transition-all cursor-pointer group">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">{stat.title}</p>
                      <p className="text-2xl font-bold">{stat.value}</p>
                      {stat.change && (
                        <div className="flex items-center gap-1 mt-2">
                          <span
                            className={`text-xs font-semibold ${
                              stat.trend === 'up' ? 'text-green-500' : 'text-red-500'
                            }`}
                          >
                            {stat.change}
                          </span>
                          <span className="text-xs text-muted-foreground">this month</span>
                        </div>
                      )}
                    </div>
                    <div className="p-3 rounded-lg bg-accent/10 text-accent group-hover:bg-accent/20 transition-colors">
                      {stat.icon}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Main Content Grid */}
        <motion.div variants={container} className="grid gap-6 lg:grid-cols-3">
          {/* Recent Activities */}
          <motion.div variants={item} className="lg:col-span-2">
            <Card className="border border-border/40">
              <CardHeader>
                <CardTitle>Recent Activities</CardTitle>
                <CardDescription>Latest updates from your talent pipeline</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivities.map((activity) => (
                    <motion.div
                      key={activity.id}
                      whileHover={{ x: 4 }}
                      className="flex gap-4 p-3 rounded-lg hover:bg-muted/30 transition-colors cursor-pointer"
                    >
                      <div className="flex-shrink-0">
                        <div className={`p-2.5 rounded-lg ${getStatusColor(activity.status)}`}>
                          {activity.type === 'interview' && <Calendar className="w-4 h-4" />}
                          {activity.type === 'application' && <Users className="w-4 h-4" />}
                          {activity.type === 'message' && <MessageSquare className="w-4 h-4" />}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">{activity.title}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {activity.description}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className="text-xs">
                          {activity.status.replace('_', ' ')}
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">{activity.timestamp}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Quick Actions */}
          <motion.div variants={item}>
            <Card className="border border-border/40 h-full">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common tasks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full justify-start bg-accent/10 text-accent hover:bg-accent/20">
                  <Briefcase className="w-4 h-4 mr-2" />
                  Post a Job
                </Button>
                <Button className="w-full justify-start bg-accent/10 text-accent hover:bg-accent/20">
                  <Users className="w-4 h-4 mr-2" />
                  View Candidates
                </Button>
                <Button className="w-full justify-start bg-accent/10 text-accent hover:bg-accent/20">
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Interview
                </Button>
                <Button className="w-full justify-start bg-accent/10 text-accent hover:bg-accent/20">
                  <BarChart3 className="w-4 h-4 mr-2" />
                  View Analytics
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Chart Section */}
        <motion.div variants={item}>
          <Card className="border border-border/40">
            <CardHeader>
              <CardTitle>Pipeline Performance</CardTitle>
              <CardDescription>Hiring funnel metrics over the last 30 days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80 bg-gradient-to-br from-blue-primary/5 to-accent/5 rounded-lg flex items-center justify-center border border-border/40">
                <div className="text-center text-muted-foreground">
                  <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Chart visualization coming soon</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </AppLayout>
  )
}
