'use client'

import { ReactNode, useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function AppShell({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  // Close sidebar on mobile when route changes
  useEffect(() => {
    setMounted(true)
  }, [])

  // Don't show layout on login page or while loading
  if (isLoading || !isAuthenticated) {
    return <>{children}</>
  }

  if (!mounted) {
    return null
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - with responsive behavior */}
      <div className="hidden md:block md:w-64 md:flex-shrink-0 border-r border-gray-200 bg-white">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 md:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar />
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* TopBar with menu button for mobile */}
        <TopBar onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="h-full px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-7xl h-full">{children}</div>
          </div>
        </main>
      </div>
    </div>
  )
}
