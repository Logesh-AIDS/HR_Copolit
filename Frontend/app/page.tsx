'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Zap, Users, BarChart3, Brain } from 'lucide-react'
import { Button } from '@/components/ui/button'

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
    },
  },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

const features = [
  {
    icon: <Brain className="w-6 h-6" />,
    title: 'AI-Powered Insights',
    description: 'Intelligent talent matching and skill assessment powered by advanced AI',
  },
  {
    icon: <Zap className="w-6 h-6" />,
    title: 'Real-Time Interviews',
    description: 'Conduct live interviews with AI-assisted transcription and evaluation',
  },
  {
    icon: <Users className="w-6 h-6" />,
    title: 'Talent Pipeline',
    description: 'Manage candidate relationships with intelligent pipeline analytics',
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: 'Advanced Analytics',
    description: 'Deep insights into hiring metrics and talent intelligence',
  },
]

export default function Page() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            y: [0, 100, 0],
          }}
          transition={{ duration: 20, repeat: Infinity }}
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-gradient-to-br from-blue-primary/20 to-accent/20 blur-3xl"
        />
        <motion.div
          animate={{
            y: [0, -100, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, delay: 1 }}
          className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-gradient-to-br from-accent/20 to-cyan/20 blur-3xl"
        />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-30 border-b border-border/20 bg-background/50 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-primary to-accent flex items-center justify-center text-white font-bold">
                T
              </div>
              <span className="font-bold text-lg group-hover:text-accent transition-colors">TalentOS</span>
            </Link>

            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/auth/login')}
                className="px-4 py-2 text-sm font-medium text-foreground hover:text-accent transition-colors"
              >
                Sign In
              </button>
              <Button
                onClick={() => router.push('/auth/signup')}
                className="bg-accent hover:bg-accent/90 text-accent-foreground"
              >
                Get Started
              </Button>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6">
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="max-w-4xl mx-auto text-center space-y-8"
          >
            <motion.div variants={item} className="space-y-4">
              <h1 className="text-5xl md:text-6xl font-bold text-balance leading-tight">
                AI-Native Talent{' '}
                <span className="bg-gradient-to-r from-blue-primary via-sky to-accent bg-clip-text text-transparent">
                  Intelligence Platform
                </span>
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
                Transform your recruitment process with advanced AI-powered talent intelligence,
                real-time interviews, and predictive analytics.
              </p>
            </motion.div>

            <motion.div variants={item} className="flex items-center justify-center gap-4 flex-wrap">
              <Button
                size="lg"
                className="bg-accent hover:bg-accent/90 text-accent-foreground px-8"
                onClick={() => router.push('/auth/signup')}
              >
                Start Free Trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
              <Button variant="outline" size="lg" className="px-8">
                Watch Demo
              </Button>
            </motion.div>

            {/* Hero Image */}
            <motion.div
              variants={item}
              className="mt-12 rounded-xl border border-border/40 overflow-hidden bg-gradient-to-br from-card to-muted/20"
            >
              <div className="aspect-video bg-gradient-to-br from-blue-primary/10 via-accent/10 to-cyan/10 flex items-center justify-center">
                <div className="text-center space-y-4">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent/10">
                    <Zap className="w-8 h-8 text-accent" />
                  </div>
                  <p className="text-muted-foreground">Premium interface coming soon</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-6 border-t border-border/40">
          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="max-w-6xl mx-auto"
          >
            <motion.h2
              variants={item}
              className="text-4xl font-bold text-center mb-16 text-balance"
            >
              Powerful Features for Modern Talent Teams
            </motion.h2>

            <div className="grid md:grid-cols-2 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  variants={item}
                  whileHover={{ y: -4, scale: 1.02 }}
                  className="p-8 rounded-xl border border-border/40 bg-card/50 backdrop-blur-sm hover:border-accent/50 hover:bg-card/80 transition-all"
                >
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-accent/10 text-accent mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-6 border-t border-border/40">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-2xl mx-auto text-center space-y-8 rounded-xl border border-border/40 bg-card/50 backdrop-blur-sm p-12"
          >
            <h2 className="text-3xl font-bold">
              Ready to revolutionize your talent strategy?
            </h2>
            <p className="text-lg text-muted-foreground">
              Join leading companies using TalentOS to transform their hiring process.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Button
                size="lg"
                className="bg-accent hover:bg-accent/90 text-accent-foreground px-8"
                onClick={() => router.push('/auth/signup')}
              >
                Get Started Now
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </motion.div>
        </section>

        {/* Footer */}
        <footer className="border-t border-border/40 py-8 px-6 text-center text-muted-foreground">
          <p>&copy; 2024 TalentOS. All rights reserved.</p>
        </footer>
      </div>
    </div>
  )
}
