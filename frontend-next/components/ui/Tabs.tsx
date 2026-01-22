'use client'

import React, { useState } from 'react'
import { clsx } from 'clsx'

interface Tab {
  id: string
  label: string
  content: React.ReactNode
  icon?: React.ReactNode
  disabled?: boolean
}

interface TabsProps {
  tabs: Tab[]
  defaultTab?: string
  variant?: 'line' | 'pill'
  onChange?: (tabId: string) => void
  className?: string
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  defaultTab = tabs[0]?.id,
  variant = 'line',
  onChange,
  className,
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab)

  const handleTabChange = (tabId: string) => {
    if (!tabs.find((t) => t.id === tabId)?.disabled) {
      setActiveTab(tabId)
      onChange?.(tabId)
    }
  }

  const activeTabData = tabs.find((t) => t.id === activeTab)

  return (
    <div className={clsx('w-full', className)}>
      {/* Tab List */}
      <div
        className={clsx(
          'flex items-center border-b border-gray-200 dark:border-gray-700',
          variant === 'pill' && 'gap-2 border-b-0 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg'
        )}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            disabled={tab.disabled}
            className={clsx(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-950',
              'disabled:cursor-not-allowed disabled:opacity-50',
              activeTab === tab.id
                ? variant === 'pill'
                  ? 'bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 rounded-md shadow-sm'
                  : 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400'
                : variant === 'pill'
                  ? 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                  : 'text-gray-600 dark:text-gray-400 border-b-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-900 dark:hover:text-gray-100'
            )}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-disabled={tab.disabled}
          >
            {tab.icon && <span>{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-6 animate-in fade-in-50 duration-200">
        {activeTabData && <div role="tabpanel">{activeTabData.content}</div>}
      </div>
    </div>
  )
}

Tabs.displayName = 'Tabs'
