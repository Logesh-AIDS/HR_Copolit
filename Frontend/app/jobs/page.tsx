'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, Filter, MoreVertical, Users, TrendingUp } from 'lucide-react'
import { AppLayout } from '@/components/layout/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface Job {
  id: string
  title: string
  department: string
  status: 'open' | 'closed' | 'draft'
  applications: number
  interviews: number
  salary?: string
  postedDate: string
}

const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior Full-Stack Engineer',
    department: 'Engineering',
    status: 'open',
    applications: 47,
    interviews: 12,
    salary: '$150k - $200k',
    postedDate: '2 weeks ago',
  },
  {
    id: '2',
    title: 'Product Manager',
    department: 'Product',
    status: 'open',
    applications: 28,
    interviews: 5,
    salary: '$120k - $160k',
    postedDate: '3 weeks ago',
  },
  {
    id: '3',
    title: 'DevOps Engineer',
    department: 'Infrastructure',
    status: 'open',
    applications: 35,
    interviews: 8,
    salary: '$130k - $180k',
    postedDate: '1 week ago',
  },
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'open':
      return 'bg-green-500/10 text-green-600 dark:text-green-400'
    case 'closed':
      return 'bg-red-500/10 text-red-600 dark:text-red-400'
    case 'draft':
      return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
    default:
      return 'bg-gray-500/10 text-gray-600 dark:text-gray-400'
  }
}

export default function JobsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredJobs = mockJobs.filter((j) =>
    j.title.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Jobs</h1>
            <p className="text-muted-foreground mt-1">Manage and post job openings</p>
          </div>
          <Button className="bg-accent hover:bg-accent/90 text-accent-foreground">
            Post New Job
          </Button>
        </div>

        {/* Search and Filter */}
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search jobs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" className="gap-2">
            <Filter className="w-4 h-4" />
            Filter
          </Button>
        </div>

        {/* Jobs List */}
        <div className="space-y-3">
          {filteredJobs.length === 0 ? (
            <Card className="border border-border/40">
              <CardContent className="pt-12 pb-12 text-center">
                <p className="text-muted-foreground">No jobs found</p>
              </CardContent>
            </Card>
          ) : (
            filteredJobs.map((job, index) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="hover:border-accent/50 transition-all cursor-pointer">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold text-foreground">{job.title}</h3>
                          <Badge
                            variant="outline"
                            className={`text-xs ${getStatusColor(job.status)}`}
                          >
                            {job.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{job.department}</p>
                        {job.salary && (
                          <p className="text-sm font-medium text-accent mt-2">{job.salary}</p>
                        )}
                        <div className="flex gap-6 mt-4">
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">
                              {job.applications} applications
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">
                              {job.interviews} interviews
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-xs text-muted-foreground mb-4">{job.postedDate}</p>
                        <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                          <MoreVertical className="w-4 h-4 text-muted-foreground" />
                        </button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))
          )}
        </div>
      </motion.div>
    </AppLayout>
  )
}
