'use client'

import { useQuota } from '../../hooks/useQuota'
import { useTheme } from '../providers/ThemeProvider'
import Badge from '../ui/Badge'

interface TopBarProps {
  onSidebarToggle?: () => void
}

export default function TopBar({ onSidebarToggle }: TopBarProps) {
  const { quota, conversionsExceeded, conversionsNearlyFull, exportsExceeded, exportsNearlyFull } = useQuota()
  const { theme, toggleTheme } = useTheme()

  if (!quota) return null

  const conversionPercentage = Math.min(
    Math.round((quota.conversions_used / quota.conversions_limit) * 100),
    100
  )
  const exportPercentage = Math.min(
    Math.round((quota.exports_used / quota.exports_limit) * 100),
    100
  )

  const getTierColor = () => {
    switch (quota.tier) {
      case 'pro':
        return 'text-amber-600 dark:text-amber-400'
      case 'enterprise':
        return 'text-purple-600 dark:text-purple-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getTierIcon = () => {
    switch (quota.tier) {
      case 'pro':
        return '⭐'
      case 'enterprise':
        return '🚀'
      default:
        return '📦'
    }
  }

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-soft dark:shadow-md transition-colors duration-200">
      <div className="px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-4">
          {/* Mobile Menu Button */}
          <button
            onClick={onSidebarToggle}
            className="md:hidden p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Toggle menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          {/* Tier Badge */}
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getTierIcon()}</span>
            <div>
              <h2 className={`text-sm font-semibold ${getTierColor()}`}>
                {quota.tier === 'free' && 'Free Tier'}
                {quota.tier === 'pro' && 'Pro Tier'}
                {quota.tier === 'enterprise' && 'Enterprise Tier'}
              </h2>
            </div>
          </div>

          {/* Quota Usage */}
          <div className="flex items-center gap-6 ml-auto">
            {/* Conversions Quota */}
            <div className="flex flex-col gap-1 min-w-fit">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Conversions</span>
                <Badge variant="info" size="sm">
                  {quota.conversions_used}/{quota.conversions_limit}
                </Badge>
              </div>
              <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    conversionsExceeded
                      ? 'bg-red-600'
                      : conversionsNearlyFull
                        ? 'bg-yellow-600'
                        : 'bg-green-600'
                  }`}
                  style={{ width: `${conversionPercentage}%` }}
                />
              </div>
            </div>

            {/* Exports Quota */}
            <div className="hidden sm:flex flex-col gap-1 min-w-fit">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Exports</span>
                <Badge variant="info" size="sm">
                  {quota.exports_used}/{quota.exports_limit}
                </Badge>
              </div>
              <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    exportsExceeded
                      ? 'bg-red-600'
                      : exportsNearlyFull
                        ? 'bg-yellow-600'
                        : 'bg-green-600'
                  }`}
                  style={{ width: `${exportPercentage}%` }}
                />
              </div>
            </div>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all duration-200 hover:scale-105"
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? (
              // Moon icon for dark mode
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            ) : (
              // Sun icon for light mode
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
