'use client'

import React, { useState } from 'react'
import { Search, Bell, Moon, Sun, Command } from 'lucide-react'
import { useUiStore } from '@/lib/store'
import { Input } from '@/components/ui/input'
import { motion } from 'framer-motion'

export function Header() {
  const { theme, toggleTheme } = useUiStore()
  const [showSearch, setShowSearch] = useState(false)

  return (
    <header className="sticky top-0 z-30 w-full border-b border-border/40 bg-card/50 backdrop-blur-md">
      <div className="flex items-center justify-between h-16 px-6 gap-4">
        {/* Search */}
        <div className="flex-1 max-w-md">
          {showSearch ? (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: '100%', opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="relative"
            >
              <Input
                placeholder="Search candidates, jobs..."
                className="w-full"
                autoFocus
                onBlur={() => setShowSearch(false)}
              />
              <Command className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            </motion.div>
          ) : (
            <button
              onClick={() => setShowSearch(true)}
              className="hidden md:flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/50 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors w-full"
            >
              <Search className="w-4 h-4" />
              <span className="text-sm">Search...</span>
              <kbd className="ml-auto text-xs px-2 py-1 rounded bg-background/50 border border-border/40">
                ⌘K
              </kbd>
            </button>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Notifications */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative p-2 rounded-lg hover:bg-muted transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5 text-muted-foreground hover:text-foreground transition-colors" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-accent rounded-full animate-pulse" />
          </motion.button>

          {/* Theme toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-muted transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-muted-foreground hover:text-foreground transition-colors" />
            ) : (
              <Moon className="w-5 h-5 text-muted-foreground hover:text-foreground transition-colors" />
            )}
          </motion.button>
        </div>
      </div>
    </header>
  )
}
