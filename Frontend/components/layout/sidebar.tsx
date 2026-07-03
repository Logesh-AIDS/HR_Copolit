'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  Users,
  Briefcase,
  Video,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react'
import { useUiStore, useAuthStore } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

interface NavItem {
  label: string
  href: string
  icon: React.ReactNode
  badge?: number
}

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUiStore()
  const { user } = useAuthStore()
  const pathname = usePathname()

  const navItems: NavItem[] = [
    {
      label: 'Dashboard',
      href: '/dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
    },
    {
      label: 'Candidates',
      href: '/candidates',
      icon: <Users className="w-4 h-4" />,
    },
    {
      label: 'Jobs',
      href: '/jobs',
      icon: <Briefcase className="w-4 h-4" />,
    },
    {
      label: 'Interviews',
      href: '/interviews',
      icon: <Video className="w-4 h-4" />,
    },
    {
      label: 'Analytics',
      href: '/analytics',
      icon: <BarChart3 className="w-4 h-4" />,
    },
  ]

  const isActive = (href: string) => pathname === href || pathname?.startsWith(href + '/')

  return (
    <>
      {/* Mobile menu toggle */}
      <button
        onClick={toggleSidebar}
        className="md:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-card border border-border/40 hover:bg-muted transition-colors"
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Overlay for mobile */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="md:hidden fixed inset-0 bg-black/20 backdrop-blur-sm z-30"
            onClick={toggleSidebar}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          x: sidebarOpen ? 0 : -320,
        }}
        transition={{ duration: 0.3, type: 'spring', stiffness: 200, damping: 30 }}
        className={cn(
          'fixed md:sticky top-0 h-screen w-80 bg-card border-r border-border/40 flex flex-col z-40',
          'md:translate-x-0',
        )}
      >
        {/* Header */}
        <div className="p-6 border-b border-border/40">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-primary to-accent flex items-center justify-center text-white font-bold text-sm">
              T
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-foreground group-hover:text-accent transition-colors">
                TalentOS
              </span>
              <span className="text-xs text-muted-foreground">Talent Intelligence</span>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = isActive(item.href)
            return (
              <motion.div key={item.href} whileHover={{ x: 4 }} whileTap={{ scale: 0.98 }}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center justify-between px-4 py-3 rounded-lg transition-all duration-200',
                    active
                      ? 'bg-accent/10 text-accent border border-accent/20'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                  )}
                >
                  <div className="flex items-center gap-3">
                    {item.icon}
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold rounded-full bg-accent text-accent-foreground">
                      {item.badge}
                    </span>
                  )}
                  {active && <ChevronRight className="w-4 h-4" />}
                </Link>
              </motion.div>
            )
          })}
        </nav>

        {/* User Profile */}
        <div className="border-t border-border/40 p-4 space-y-4">
          {user && (
            <div className="flex items-center gap-3 px-2">
              <Avatar className="w-10 h-10">
                <AvatarImage src={user.avatar} alt={user.name} />
                <AvatarFallback>{user.name.charAt(0)}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate text-foreground">{user.name}</p>
                <p className="text-xs text-muted-foreground truncate">{user.email}</p>
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <Link
              href="/settings"
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Settings</span>
            </Link>
            <button className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors">
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </motion.aside>
    </>
  )
}
