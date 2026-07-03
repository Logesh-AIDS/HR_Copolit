'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Search, Filter, MoreVertical, Play, Calendar, Clock } from 'lucide-react'
import { AppLayout } from '@/components/layout/app-layout'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

interface Interview {
  id: string
  candidateName: string
  position: string
  type: 'technical' | 'behavioral' | 'coding' | 'system_design'
  status: 'scheduled' | 'completed' | 'cancelled' | 'in_progress'
  scheduledDate: string
  time: string
  score?: number
}

const mockInterviews: Interview[] = [
  {
    id: '1',
    candidateName: 'Sarah Anderson',
    position: 'Senior Full-Stack Engineer',
    type: 'technical',
    status: 'completed',
    scheduledDate: '2024-07-01',
    time: '2:00 PM',
    score: 92,
  },
  {
    id: '2',
    candidateName: 'John Smith',
    position: 'Product Manager',
    type: 'behavioral',
    status: 'scheduled',
    scheduledDate: '2024-07-05',
    time: '3:30 PM',
  },
  {
    id: '3',
    candidateName: 'Emily Johnson',
    position: 'DevOps Engineer',
    type: 'coding',
    status: 'in_progress',
    scheduledDate: '2024-07-03',
    time: '10:00 AM',
  },
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'scheduled':
      return 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
    case 'completed':
      return 'bg-green-500/10 text-green-600 dark:text-green-400'
    case 'cancelled':
      return 'bg-red-500/10 text-red-600 dark:text-red-400'
    case 'in_progress':
      return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
    default:
      return 'bg-gray-500/10 text-gray-600 dark:text-gray-400'
  }
}

const getTypeColor = (type: string) => {
  switch (type) {
    case 'technical':
      return 'bg-purple-500/10 text-purple-600 dark:text-purple-400'
    case 'behavioral':
      return 'bg-pink-500/10 text-pink-600 dark:text-pink-400'
    case 'coding':
      return 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400'
    case 'system_design':
      return 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'
    default:
      return 'bg-gray-500/10 text-gray-600 dark:text-gray-400'
  }
}

export default function InterviewsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredInterviews = mockInterviews.filter((i) =>
    i.candidateName.toLowerCase().includes(searchQuery.toLowerCase()),
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
            <h1 className="text-3xl font-bold">Interviews</h1>
            <p className="text-muted-foreground mt-1">Manage and conduct interviews</p>
          </div>
          <Button className="bg-accent hover:bg-accent/90 text-accent-foreground">
            Schedule Interview
          </Button>
        </div>

        {/* Search and Filter */}
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search interviews..."
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

        {/* Interviews List */}
        <div className="space-y-3">
          {filteredInterviews.length === 0 ? (
            <Card className="border border-border/40">
              <CardContent className="pt-12 pb-12 text-center">
                <p className="text-muted-foreground">No interviews found</p>
              </CardContent>
            </Card>
          ) : (
            filteredInterviews.map((interview, index) => (
              <motion.div
                key={interview.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="hover:border-accent/50 transition-all">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex gap-4 flex-1">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback>{interview.candidateName.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <h3 className="font-semibold text-foreground">
                            {interview.candidateName}
                          </h3>
                          <p className="text-sm text-muted-foreground mt-1">
                            {interview.position}
                          </p>
                          <div className="flex gap-2 mt-3">
                            <Badge
                              variant="outline"
                              className={`text-xs ${getTypeColor(interview.type)}`}
                            >
                              {interview.type.replace('_', ' ')}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={`text-xs ${getStatusColor(interview.status)}`}
                            >
                              {interview.status}
                            </Badge>
                          </div>
                          <div className="flex gap-6 mt-3">
                            <div className="flex items-center gap-1 text-sm text-muted-foreground">
                              <Calendar className="w-4 h-4" />
                              {interview.scheduledDate}
                            </div>
                            <div className="flex items-center gap-1 text-sm text-muted-foreground">
                              <Clock className="w-4 h-4" />
                              {interview.time}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0 ml-4">
                        {interview.score && (
                          <div>
                            <p className="text-2xl font-bold text-accent">{interview.score}%</p>
                            <p className="text-xs text-muted-foreground">Score</p>
                          </div>
                        )}
                        <div className="flex gap-2 mt-4">
                          {interview.status === 'scheduled' && (
                            <Link href={`/interviews/${interview.id}`}>
                              <Button size="sm" className="gap-1 bg-accent hover:bg-accent/90">
                                <Play className="w-3 h-3" />
                                Start
                              </Button>
                            </Link>
                          )}
                          {interview.status === 'in_progress' && (
                            <Link href={`/interviews/${interview.id}`}>
                              <Button size="sm" className="gap-1 bg-accent hover:bg-accent/90">
                                <Play className="w-3 h-3" />
                                Continue
                              </Button>
                            </Link>
                          )}
                          {interview.status === 'completed' && (
                            <Link href={`/interviews/${interview.id}`}>
                              <Button size="sm" variant="outline">
                                View
                              </Button>
                            </Link>
                          )}
                          <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                            <MoreVertical className="w-4 h-4 text-muted-foreground" />
                          </button>
                        </div>
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
