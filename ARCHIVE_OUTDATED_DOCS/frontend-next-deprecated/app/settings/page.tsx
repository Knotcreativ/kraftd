'use client'

import { useAuth } from '@/hooks/useAuth'
import { useQuota } from '@/hooks/useQuota'

export default function SettingsPage() {
  const { isAuthenticated } = useAuth()
  const { quota, isLoading } = useQuota()

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">Manage your account and preferences</p>
      </div>

      {/* Account Section */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Account</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Authentication Status
            </label>
            <div className="mt-1 flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${isAuthenticated ? 'bg-green-600' : 'bg-red-600'}`}></div>
              <span className="text-gray-900 dark:text-gray-100">
                {isAuthenticated ? 'Authenticated' : 'Not authenticated'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quota Section */}
      {!isLoading && quota && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Quota & Usage</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {/* Tier */}
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Current Tier</p>
              <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100 capitalize">
                {quota.tier}
              </p>
            </div>

            {/* Conversions */}
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Conversions</p>
              <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
                {quota.conversions_used} / {quota.conversions_limit}
              </p>
              <div className="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: `${Math.min(
                      (quota.conversions_used / quota.conversions_limit) * 100,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>

            {/* Exports */}
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Exports</p>
              <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
                {quota.exports_used} / {quota.exports_limit}
              </p>
              <div className="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{
                    width: `${Math.min(
                      (quota.exports_used / quota.exports_limit) * 100,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>

          {/* API Calls */}
          <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">API Calls</p>
            <div className="flex items-center justify-between">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {quota.api_calls_used} / {quota.api_calls_limit}
              </p>
              <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full"
                  style={{
                    width: `${Math.min(
                      (quota.api_calls_used / quota.api_calls_limit) * 100,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preferences Section */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Preferences</h2>
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600"
            />
            <span className="text-gray-900 dark:text-gray-100">Email notifications for conversions</span>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600"
            />
            <span className="text-gray-900 dark:text-gray-100">Weekly usage summary</span>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600"
            />
            <span className="text-gray-900 dark:text-gray-100">Marketing emails</span>
          </label>
        </div>
      </div>

      {/* API Keys Section */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">API Integration</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Use your JWT token to authenticate API requests. Keep it secure and never share it publicly.
        </p>
        <button className="btn btn-secondary">View API Documentation</button>
      </div>
    </div>
  )
}
