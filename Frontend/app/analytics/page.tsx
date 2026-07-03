'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, Users, Clock } from 'lucide-react'
import { AppLayout } from '@/components/layout/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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

interface MetricCard {
  title: string
  value: string | number
  change?: string
  trend?: 'up' | 'down'
  icon: React.ReactNode
}

const metrics: MetricCard[] = [
  {
    title: 'Average Interview Score',
    value: '82.5%',
    change: '+2.3%',
    trend: 'up',
    icon: <BarChart3 className="w-5 h-5" />,
  },
  {
    title: 'Time to Hire',
    value: '18 days',
    change: '-3 days',
    trend: 'down',
    icon: <Clock className="w-5 h-5" />,
  },
  {
    title: 'Conversion Rate',
    value: '32%',
    change: '+5%',
    trend: 'up',
    icon: <TrendingUp className="w-5 h-5" />,
  },
  {
    title: 'Top Skill',
    value: 'React',
    change: '89 candidates',
    icon: <Users className="w-5 h-5" />,
  },
]

export default function AnalyticsPage() {
  return (
    <AppLayout>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
        {/* Page Header */}
        <motion.div variants={item} className="space-y-2">
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">Deep insights into your hiring metrics and talent intelligence</p>
        </motion.div>

        {/* Key Metrics */}
        <motion.div
          variants={container}
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
        >
          {metrics.map((metric) => (
            <motion.div key={metric.title} variants={item}>
              <Card className="hover:border-accent/50 transition-all cursor-pointer group">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">{metric.title}</p>
                      <p className="text-2xl font-bold">{metric.value}</p>
                      {metric.change && (
                        <div className="flex items-center gap-1 mt-2">
                          <span
                            className={`text-xs font-semibold ${
                              metric.trend === 'up' || (metric.title.includes('Conversion') && metric.trend === 'up')
                                ? 'text-green-500'
                                : 'text-green-500'
                            }`}
                          >
                            {metric.change}
                          </span>
                          <span className="text-xs text-muted-foreground">this month</span>
                        </div>
                      )}
                    </div>
                    <div className="p-3 rounded-lg bg-accent/10 text-accent group-hover:bg-accent/20 transition-colors">
                      {metric.icon}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Charts Grid */}
        <motion.div variants={container} className="grid gap-6 lg:grid-cols-2">
          {/* Hiring Funnel */}
          <motion.div variants={item}>
            <Card className="border border-border/40">
              <CardHeader>
                <CardTitle>Hiring Funnel</CardTitle>
                <CardDescription>Candidate progression through stages</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { stage: 'Applications', count: 342, percentage: 100 },
                    { stage: 'Screening', count: 145, percentage: 42 },
                    { stage: 'Technical Interview', count: 68, percentage: 20 },
                    { stage: 'Offer', count: 18, percentage: 5 },
                  ].map((item) => (
                    <div key={item.stage}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-foreground">{item.stage}</span>
                        <span className="text-sm text-muted-foreground">{item.count}</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${item.percentage}%` }}
                          transition={{ delay: 0.2, duration: 1 }}
                          className="h-full bg-gradient-to-r from-accent to-accent/50"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Skill Distribution */}
          <motion.div variants={item}>
            <Card className="border border-border/40">
              <CardHeader>
                <CardTitle>Top Skills</CardTitle>
                <CardDescription>Most demanded skills in pipeline</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { skill: 'React', count: 89 },
                    { skill: 'Python', count: 76 },
                    { skill: 'AWS', count: 64 },
                    { skill: 'TypeScript', count: 58 },
                    { skill: 'PostgreSQL', count: 52 },
                  ].map((item) => (
                    <div key={item.skill} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge variant="secondary">{item.skill}</Badge>
                      </div>
                      <span className="text-sm font-medium text-foreground">{item.count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Performance Metrics */}
        <motion.div variants={item}>
          <Card className="border border-border/40">
            <CardHeader>
              <CardTitle>Interview Performance</CardTitle>
              <CardDescription>Score distribution across interviews</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-blue-primary/5 to-accent/5 rounded-lg flex items-center justify-center border border-border/40">
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
