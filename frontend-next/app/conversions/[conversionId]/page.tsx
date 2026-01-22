'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, useRouter } from 'next/navigation'
import { getConversion } from '../../../../lib/api/conversions'
import { getConversionSchema } from '../../../../lib/api/schema'
import { getConversionSummary } from '../../../../lib/api/summary'
import { getConversionOutputs } from '../../../../lib/api/outputs'
import { useQuota } from '../../../../hooks/useQuota'
import type { Schema, Summary, Output } from '../../../../lib/types'

type TabType = 'schema' | 'summary' | 'outputs'

export default function ConversionWorkspacePage() {
  const params = useParams()
  const conversionId = params.conversionId as string
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<TabType>('schema')
  const { quota } = useQuota()

  const { data: conversion, isLoading: convLoading, error: convError } = useQuery({
    queryKey: ['conversion', conversionId],
    queryFn: () => getConversion(conversionId),
  })

  const { data: schema, isLoading: schemaLoading } = useQuery({
    queryKey: ['schema', conversionId],
    queryFn: () => getConversionSchema(conversionId),
    enabled: !!conversion && activeTab === 'schema',
  })

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['summary', conversionId],
    queryFn: () => getConversionSummary(conversionId),
    enabled: !!conversion && activeTab === 'summary',
  })

  const { data: outputs, isLoading: outputsLoading } = useQuery({
    queryKey: ['outputs', conversionId],
    queryFn: () => getConversionOutputs(conversionId),
    enabled: !!conversion && activeTab === 'outputs',
  })

  if (convLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-300 dark:border-gray-600 border-t-blue-600"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading conversion...</p>
        </div>
      </div>
    )
  }

  if (convError || !conversion) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.back()}
          className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1"
        >
          ← Back
        </button>
        <div className="rounded-md bg-red-50 dark:bg-red-950 p-4">
          <p className="text-sm font-medium text-red-800 dark:text-red-200">
            Failed to load conversion. Please try again.
          </p>
        </div>
      </div>
    )
  }

  const tabs: { id: TabType; label: string }[] = [
    { id: 'schema', label: 'Schema' },
    { id: 'summary', label: 'Summary' },
    { id: 'outputs', label: 'Outputs' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => router.back()}
          className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1 mb-4"
        >
          ← Back to Conversions
        </button>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">{conversion.document_name}</h1>
        <div className="mt-2 flex items-center gap-4">
          <span className="inline-flex items-center rounded-full bg-green-100 dark:bg-green-900 px-3 py-1 text-sm font-medium text-green-800 dark:text-green-200">
            {conversion.status}
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {conversion.document_type} • {conversion.size_bytes ? (conversion.size_bytes / 1024).toFixed(2) + ' KB' : 'Unknown size'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex gap-8 px-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-900 dark:hover:text-gray-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="card">
        {activeTab === 'schema' && (
          <SchemaTab schema={schema} isLoading={schemaLoading} />
        )}
        {activeTab === 'summary' && (
          <SummaryTab summary={summary} isLoading={summaryLoading} />
        )}
        {activeTab === 'outputs' && (
          <OutputsTab outputs={outputs} isLoading={outputsLoading} />
        )}
      </div>

      {/* Quota Info */}
      {quota && (
        <div className="rounded-md bg-blue-50 dark:bg-blue-950 p-4 text-sm text-blue-800 dark:text-blue-200">
          <strong>Quota:</strong> {quota.conversions_used} / {quota.conversions_limit} conversions used
        </div>
      )}
    </div>
  )
}

function SchemaTab({
  schema,
  isLoading,
}: {
  schema?: Schema
  isLoading: boolean
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading schema...</p>
        </div>
      </div>
    )
  }

  if (!schema) {
    return <p className="text-gray-600">No schema available for this conversion.</p>
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Generated Schema</h3>
        <pre className="bg-gray-50 p-4 rounded border border-gray-200 overflow-auto max-h-96 text-sm">
          {JSON.stringify(schema.content, null, 2)}
        </pre>
      </div>
      <button className="btn btn-primary">Edit Schema</button>
    </div>
  )
}

function SummaryTab({
  summary,
  isLoading,
}: {
  summary?: Summary
  isLoading: boolean
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading summary...</p>
        </div>
      </div>
    )
  }

  if (!summary) {
    return <p className="text-gray-600">No summary available for this conversion.</p>
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Document Summary</h3>
        <p className="text-gray-700 whitespace-pre-wrap">{summary.content}</p>
      </div>
      <button className="btn btn-primary">Regenerate Summary</button>
    </div>
  )
}

function OutputsTab({
  outputs,
  isLoading,
}: {
  outputs?: Output[]
  isLoading: boolean
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading outputs...</p>
        </div>
      </div>
    )
  }

  if (!outputs || outputs.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600 mb-4">No outputs generated yet.</p>
        <button className="btn btn-primary">Generate Output</button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4">
        {outputs.map((output) => (
          <div key={output.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">
                  {output.format.toUpperCase()} Export
                </h4>
                <p className="text-sm text-gray-600">
                  Generated {new Date(output.generated_at).toLocaleDateString()}
                </p>
              </div>
              <button className="btn btn-secondary text-sm">Download</button>
            </div>
          </div>
        ))}
      </div>
      <button className="btn btn-primary">Generate New Output</button>
    </div>
  )
}
