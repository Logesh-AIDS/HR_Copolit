'use client'

import React, { ReactNode } from 'react'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { useUiStore } from '@/lib/store'
import { motion } from 'framer-motion'

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const { sidebarOpen } = useUiStore()

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Page content */}
        <motion.main
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.3 }}
          className="flex-1 overflow-y-auto"
        >
          <div className="p-6">{children}</div>
        </motion.main>
      </div>
    </div>
  )
}
