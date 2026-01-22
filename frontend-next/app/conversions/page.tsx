'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { getConversions } from '../../lib/api/conversions'
import type { Conversion } from '../../lib/types'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import { Card, CardContent, CardDescription } from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import { CardSkeleton } from '../../components/ui/Skeleton'

export default function ConversionsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'processing'>('all')

  const { data: conversions = [], isLoading, error } = useQuery({
    queryKey: ['conversions'],
    queryFn: getConversions,
  })

  const filteredConversions = useMemo(() => {
    return conversions.filter((conv) => {
      const matchesSearch =
        conv.document_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (conv.file_path && conv.file_path.toLowerCase().includes(searchTerm.toLowerCase()))
      const matchesStatus =
        filterStatus === 'all' ||
        (filterStatus === 'completed' && conv.status === 'active') ||
        (filterStatus === 'processing' && conv.status !== 'active')
      return matchesSearch && matchesStatus
    })
  }, [conversions, searchTerm, filterStatus])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">Conversions</h1>
          <CardDescription className="mt-2">
            Manage and organize your document conversions
          </CardDescription>
        </div>
        <Link href="/conversions/new">
          <Button variant="primary" size="md">
            New Conversion
          </Button>
        </Link>
      </div>

      {/* Search and Filter Card */}
      <Card>
        <CardContent className="space-y-4 pt-6">
          <Input
            placeholder="Search by name or filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="md"
            leftIcon={
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            }
          />

          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-2">
            {(['all', 'completed', 'processing'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  filterStatus === status
                    ? 'bg-blue-600 text-white shadow-soft-md'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                {status === 'all' && '✓ All'}
                {status === 'completed' && '✓ Completed'}
                {status === 'processing' && '⏳ Processing'}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Conversions Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <Card className="border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950">
          <CardContent className="flex items-center gap-3 pt-6">
            <svg className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-red-900 dark:text-red-100">Failed to load conversions</p>
              <p className="text-sm text-red-700 dark:text-red-300">Please try again or contact support</p>
            </div>
          </CardContent>
        </Card>
      ) : filteredConversions.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <svg
              className="h-12 w-12 text-gray-400 dark:text-gray-500 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">No conversions found</h3>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              {searchTerm
                ? 'No conversions match your search criteria.'
                : 'Get started by creating your first document conversion.'}
            </p>
            {!searchTerm && (
              <Link href="/conversions/new" className="mt-4">
                <Button variant="primary">Create Your First Conversion</Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredConversions.map((conversion) => (
            <ConversionCard key={conversion.id} conversion={conversion} />
          ))}
        </div>
      )}
    </div>
  )
}

function ConversionCard({ conversion }: { conversion: Conversion }) {
  const statusConfig = {
    pending: { variant: 'warning' as const, icon: '⏳' },
    processing: { variant: 'info' as const, icon: '⚙️' },
    completed: { variant: 'success' as const, icon: '✓' },
    failed: { variant: 'error' as const, icon: '✕' },
  }

  const config = statusConfig[conversion.status as keyof typeof statusConfig] || statusConfig.pending
  const createdDate = new Date(conversion.created_at)
  const formattedDate = createdDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <Link href={`/conversions/${conversion.id}`}>
      <Card
        interactive
        hoverable
        className="group transition-all duration-200 transform hover:scale-105 h-full flex flex-col"
      >
        {/* Card Header with Status */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">
              {conversion.document_name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 truncate">{conversion.document_type}</p>
          </div>
          <Badge variant={config.variant} size="sm" className="flex-shrink-0 ml-2">
            {config.icon}
          </Badge>
        </div>

        {/* Card Body */}
        <div className="flex-1 space-y-3 text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>{formattedDate}</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <span className="uppercase text-xs font-medium">{conversion.document_type}</span>
          </div>
        </div>

        {/* Footer Action */}
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs font-medium text-blue-600 dark:text-blue-400 group-hover:text-blue-700 dark:group-hover:text-blue-300 flex items-center gap-1">
            View Details
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </Card>
    </Link>
  )
}
