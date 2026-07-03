'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Bell, Lock, User, CreditCard, LogOut, Save } from 'lucide-react'
import { AppLayout } from '@/components/layout/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface SettingsTab {
  id: string
  label: string
  icon: React.ReactNode
}

const tabs: SettingsTab[] = [
  { id: 'profile', label: 'Profile', icon: <User className="w-4 h-4" /> },
  { id: 'notifications', label: 'Notifications', icon: <Bell className="w-4 h-4" /> },
  { id: 'security', label: 'Security', icon: <Lock className="w-4 h-4" /> },
  { id: 'billing', label: 'Billing', icon: <CreditCard className="w-4 h-4" /> },
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setIsSaving(false)
  }

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-6 max-w-4xl"
      >
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Manage your account and preferences</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-border/40 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-accent text-accent'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === 'profile' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <Card className="border border-border/40">
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Update your personal information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">First Name</label>
                    <Input placeholder="John" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Last Name</label>
                    <Input placeholder="Doe" />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">Email</label>
                  <Input placeholder="john@example.com" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">Company</label>
                  <Input placeholder="Your Company" />
                </div>
                <div className="flex justify-end">
                  <Button
                    className="bg-accent hover:bg-accent/90 text-accent-foreground gap-2"
                    onClick={handleSave}
                    disabled={isSaving}
                  >
                    <Save className="w-4 h-4" />
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {activeTab === 'notifications' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <Card className="border border-border/40">
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Choose how you want to be notified</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {[
                  { name: 'Email Notifications', enabled: true },
                  { name: 'Interview Reminders', enabled: true },
                  { name: 'Application Updates', enabled: true },
                  { name: 'Weekly Digest', enabled: false },
                ].map((setting) => (
                  <div key={setting.name} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">{setting.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Receive notifications about {setting.name.toLowerCase()}
                      </p>
                    </div>
                    <input type="checkbox" defaultChecked={setting.enabled} className="w-4 h-4" />
                  </div>
                ))}
                <div className="pt-4 flex justify-end">
                  <Button
                    className="bg-accent hover:bg-accent/90 text-accent-foreground gap-2"
                    onClick={handleSave}
                    disabled={isSaving}
                  >
                    <Save className="w-4 h-4" />
                    {isSaving ? 'Saving...' : 'Save Preferences'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {activeTab === 'security' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <Card className="border border-border/40">
              <CardHeader>
                <CardTitle>Security Settings</CardTitle>
                <CardDescription>Manage your account security</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
                  <h3 className="font-medium text-foreground mb-2">Two-Factor Authentication</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Add an extra layer of security to your account
                  </p>
                  <Badge variant="outline">Not Enabled</Badge>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">Change Password</label>
                  <Input type="password" placeholder="Current password" />
                  <Input type="password" placeholder="New password" />
                  <Input type="password" placeholder="Confirm new password" />
                </div>
                <div className="flex justify-end">
                  <Button
                    className="bg-accent hover:bg-accent/90 text-accent-foreground gap-2"
                    onClick={handleSave}
                    disabled={isSaving}
                  >
                    <Save className="w-4 h-4" />
                    {isSaving ? 'Saving...' : 'Update Password'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {activeTab === 'billing' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <Card className="border border-border/40">
              <CardHeader>
                <CardTitle>Billing Information</CardTitle>
                <CardDescription>Manage your subscription and billing</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="p-4 rounded-lg bg-gradient-to-r from-accent/10 to-accent/5 border border-accent/20">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-foreground">Current Plan</h3>
                    <Badge className="bg-accent text-accent-foreground">Pro</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">$99/month - billed annually</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Renews on August 1, 2024
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Danger Zone */}
        <Card className="border border-destructive/20 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">Danger Zone</CardTitle>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" className="gap-2">
              <LogOut className="w-4 h-4" />
              Logout All Devices
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    </AppLayout>
  )
}
