'use client'

import { useState } from 'react'

interface DiffViewerProps {
  originalText: string
  modifiedText: string
  isDiff?: boolean
}

export function DiffViewer({ originalText, modifiedText, isDiff = false }: DiffViewerProps) {
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split')

  if (!isDiff) {
    return (
      <div className="space-y-4">
        <div className="border rounded-md">
          <div className="bg-gray-50 px-4 py-2 border-b">
            <h4 className="font-medium">Original Text</h4>
          </div>
          <div className="p-4">
            <pre className="whitespace-pre-wrap text-sm font-mono">
              {originalText}
            </pre>
          </div>
        </div>
      </div>
    )
  }

  const parseDiff = (diffText: string) => {
    const lines = diffText.split('\n')
    const changes: Array<{type: 'add' | 'remove' | 'context', content: string, lineNumber?: number}> = []
    
    for (const line of lines) {
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
        continue
      }
      
      if (line.startsWith('+')) {
        changes.push({ type: 'add', content: line.slice(1) })
      } else if (line.startsWith('-')) {
        changes.push({ type: 'remove', content: line.slice(1) })
      } else if (line.startsWith(' ')) {
        changes.push({ type: 'context', content: line.slice(1) })
      }
    }
    
    return changes
  }

  const changes = parseDiff(modifiedText)

  return (
    <div className="space-y-4">
      {/* View Mode Toggle */}
      <div className="flex space-x-2">
        <button
          onClick={() => setViewMode('split')}
          className={`px-3 py-1 rounded text-sm ${
            viewMode === 'split' 
              ? 'bg-primary-600 text-white' 
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          Split View
        </button>
        <button
          onClick={() => setViewMode('unified')}
          className={`px-3 py-1 rounded text-sm ${
            viewMode === 'unified' 
              ? 'bg-primary-600 text-white' 
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          Unified View
        </button>
      </div>

      {viewMode === 'split' ? (
        <div className="grid md:grid-cols-2 gap-4">
          {/* Original */}
          <div className="border rounded-md">
            <div className="bg-red-50 px-4 py-2 border-b">
              <h4 className="font-medium text-red-800">Original</h4>
            </div>
            <div className="p-4 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-mono">
                {originalText}
              </pre>
            </div>
          </div>

          {/* Modified */}
          <div className="border rounded-md">
            <div className="bg-green-50 px-4 py-2 border-b">
              <h4 className="font-medium text-green-800">Modified</h4>
            </div>
            <div className="p-4 max-h-96 overflow-y-auto">
              <div className="space-y-1">
                {changes.map((change, index) => (
                  <div
                    key={index}
                    className={`text-sm font-mono ${
                      change.type === 'add' 
                        ? 'bg-green-100 text-green-800' 
                        : change.type === 'remove'
                        ? 'bg-red-100 text-red-800'
                        : 'text-gray-700'
                    }`}
                  >
                    <span className="inline-block w-6 text-xs text-gray-500">
                      {change.type === 'add' ? '+' : change.type === 'remove' ? '-' : ' '}
                    </span>
                    {change.content}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="border rounded-md">
          <div className="bg-gray-50 px-4 py-2 border-b">
            <h4 className="font-medium">Unified Diff</h4>
          </div>
          <div className="p-4 max-h-96 overflow-y-auto">
            <div className="space-y-1">
              {changes.map((change, index) => (
                <div
                  key={index}
                  className={`text-sm font-mono ${
                    change.type === 'add' 
                      ? 'bg-green-100 text-green-800' 
                      : change.type === 'remove'
                      ? 'bg-red-100 text-red-800'
                      : 'text-gray-700'
                  }`}
                >
                  <span className="inline-block w-6 text-xs text-gray-500 mr-2">
                    {change.type === 'add' ? '+' : change.type === 'remove' ? '-' : ' '}
                  </span>
                  {change.content}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
