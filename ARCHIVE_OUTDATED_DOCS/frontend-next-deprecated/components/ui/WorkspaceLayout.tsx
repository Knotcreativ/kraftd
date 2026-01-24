'use client'

import React from 'react'
import clsx from 'clsx'

interface WorkspaceLayoutProps {
  title: string
  description?: string
  header?: React.ReactNode
  tabs?: Array<{
    id: string
    label: string
    icon?: React.ReactNode
  }>
  activeTab?: string
  onTabChange?: (tabId: string) => void
  children: React.ReactNode
  sidebar?: React.ReactNode
  footer?: React.ReactNode
  className?: string
}

const WorkspaceLayout = React.forwardRef<HTMLDivElement, WorkspaceLayoutProps>(
  (
    {
      title,
      description,
      header,
      tabs,
      activeTab,
      onTabChange,
      children,
      sidebar,
      footer,
      className,
    },
    ref
  ) => {
    const [selectedTab, setSelectedTab] = React.useState(activeTab || tabs?.[0]?.id || '')

    const handleTabChange = (tabId: string) => {
      setSelectedTab(tabId)
      onTabChange?.(tabId)
    }

    return (
      <div
        ref={ref}
        className={clsx('flex h-screen flex-col overflow-hidden bg-gray-50', className)}
      >
        {/* Header */}
        <div className="flex flex-col gap-4 border-b border-gray-200 bg-white px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {description && (
              <p className="text-gray-600">{description}</p>
            )}
          </div>
          {header}
        </div>

        {/* Tabs */}
        {tabs && tabs.length > 0 && (
          <div className="border-b border-gray-200 bg-white px-6">
            <nav className="flex gap-6" role="tablist">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={selectedTab === tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={clsx(
                    'flex items-center gap-2 border-b-2 px-1 py-4 text-sm font-medium transition-colors',
                    selectedTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  )}
                >
                  {tab.icon && <span className="h-4 w-4">{tab.icon}</span>}
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        )}

        {/* Main Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          {sidebar && (
            <aside className="w-64 overflow-y-auto border-r border-gray-200 bg-white">
              {sidebar}
            </aside>
          )}

          {/* Content */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-gray-200 bg-white px-6 py-4">
            {footer}
          </div>
        )}
      </div>
    )
  }
)

WorkspaceLayout.displayName = 'WorkspaceLayout'
export default WorkspaceLayout
