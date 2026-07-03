'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, Filter, MoreVertical, Star } from 'lucide-react'
import { AppLayout } from '@/components/layout/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

interface Candidate {
  id: string
  name: string
  role: string
  skills: string[]
  experience: number
  score: number
  status: 'new' | 'reviewing' | 'interviewed' | 'rejected'
  avatar?: string
}

const mockCandidates: Candidate[] = [
  {
    id: '1',
    name: 'Sarah Anderson',
    role: 'Senior Full-Stack Engineer',
    skills: ['React', 'Node.js', 'PostgreSQL'],
    experience: 8,
    score: 95,
    status: 'interviewed',
  },
  {
    id: '2',
    name: 'John Smith',
    role: 'Product Manager',
    skills: ['Product Strategy', 'Data Analysis', 'User Research'],
    experience: 6,
    score: 88,
    status: 'reviewing',
  },
  {
    id: '3',
    name: 'Emily Johnson',
    role: 'DevOps Engineer',
    skills: ['Kubernetes', 'AWS', 'Docker'],
    experience: 5,
    score: 85,
    status: 'new',
  },
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'new':
      return 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
    case 'reviewing':
      return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
    case 'interviewed':
      return 'bg-green-500/10 text-green-600 dark:text-green-400'
    case 'rejected':
      return 'bg-red-500/10 text-red-600 dark:text-red-400'
    default:
      return 'bg-gray-500/10 text-gray-600 dark:text-gray-400'
  }
}

export default function CandidatesPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredCandidates = mockCandidates.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()),
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
            <h1 className="text-3xl font-bold">Candidates</h1>
            <p className="text-muted-foreground mt-1">Manage and review candidates</p>
          </div>
          <Button className="bg-accent hover:bg-accent/90 text-accent-foreground">
            Add Candidate
          </Button>
        </div>

        {/* Search and Filter */}
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search candidates..."
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

        {/* Candidates List */}
        <div className="space-y-3">
          {filteredCandidates.length === 0 ? (
            <Card className="border border-border/40">
              <CardContent className="pt-12 pb-12 text-center">
                <p className="text-muted-foreground">No candidates found</p>
              </CardContent>
            </Card>
          ) : (
            filteredCandidates.map((candidate, index) => (
              <motion.div
                key={candidate.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="hover:border-accent/50 transition-all cursor-pointer">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex gap-4 flex-1">
                        <Avatar className="w-12 h-12">
                          <AvatarImage src={candidate.avatar} />
                          <AvatarFallback>{candidate.name.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-foreground">{candidate.name}</h3>
                            <Badge
                              variant="outline"
                              className={`text-xs ${getStatusColor(candidate.status)}`}
                            >
                              {candidate.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1">{candidate.role}</p>
                          <div className="flex gap-2 mt-3">
                            {candidate.skills.map((skill) => (
                              <Badge key={skill} variant="secondary" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0 ml-4">
                        <div className="flex items-center gap-2">
                          <Star className="w-4 h-4 text-accent fill-accent" />
                          <span className="text-lg font-bold text-foreground">
                            {candidate.score}%
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {candidate.experience} years
                        </p>
                        <button className="p-2 hover:bg-muted rounded-lg transition-colors mt-2">
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
