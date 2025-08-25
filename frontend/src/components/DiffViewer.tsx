'use client'

import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

interface DiffLine {
  left: string
  right: string
  type: 'add' | 'delete' | 'modify' | 'equal'
}

interface DiffViewerProps {
  originalText: string
  modifiedText: string
  title?: string
  variant?: string
}

export function DiffViewer({ originalText, modifiedText, title, variant }: DiffViewerProps) {
  const [viewMode, setViewMode] = useState<'unified' | 'side-by-side'>('side-by-side')
  const [showLineNumbers, setShowLineNumbers] = useState(true)
  const [copied, setCopied] = useState(false)
  
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  const generateSideBySide = () => {
    const originalLines = originalText.split('\n')
    const modifiedLines = modifiedText.split('\n')
    const maxLines = Math.max(originalLines.length, modifiedLines.length)
    
    const diffLines: DiffLine[] = []
    
    for (let i = 0; i < maxLines; i++) {
      const leftLine = i < originalLines.length ? originalLines[i] : ''
      const rightLine = i < modifiedLines.length ? modifiedLines[i] : ''
      
      let type: DiffLine['type'] = 'equal'
      if (leftLine !== rightLine) {
        if (leftLine && rightLine) {
          type = 'modify'
        } else if (leftLine) {
          type = 'delete'
        } else {
          type = 'add'
        }
      }
      
      diffLines.push({ left: leftLine, right: rightLine, type })
    }
    
    return diffLines
  }

  const diffLines = generateSideBySide()

  const getLineClass = (type: DiffLine['type']) => {
    switch (type) {
      case 'add':
        return 'bg-neon-green/10 border-l-4 border-neon-green/50'
      case 'delete':
        return 'bg-red-500/10 border-l-4 border-red-500/50'
      case 'modify':
        return 'bg-neon-yellow/10 border-l-4 border-neon-yellow/50'
      default:
        return ''
    }
  }

  const getTypeIcon = (type: DiffLine['type']) => {
    switch (type) {
      case 'add':
        return <span className="text-neon-green text-sm font-mono">+</span>
      case 'delete':
        return <span className="text-red-400 text-sm font-mono">-</span>
      case 'modify':
        return <span className="text-neon-yellow text-sm font-mono">~</span>
      default:
        return <span className="text-gray-500 text-sm font-mono">&nbsp;</span>
    }
  }

  return (
    <div className="neon-card rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-border">
        <div>
          <h3 className="font-display font-semibold gradient-text">
            {title || 'Text Comparison'}
          </h3>
          {variant && (
            <p className="text-sm text-neon-cyan/60 mt-1">Variant: {variant}</p>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex bg-dark-bg rounded-lg p-1">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`
                px-3 py-1 text-sm rounded transition-all duration-300
                ${viewMode === 'side-by-side' 
                  ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/50' 
                  : 'text-gray-400 hover:text-gray-200'
                }
              `}
            >
              Side by Side
            </button>
            <button
              onClick={() => setViewMode('unified')}
              className={`
                px-3 py-1 text-sm rounded transition-all duration-300
                ${viewMode === 'unified' 
                  ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/50' 
                  : 'text-gray-400 hover:text-gray-200'
                }
              `}
            >
              Unified
            </button>
          </div>
          
          <button
            onClick={() => copyToClipboard(modifiedText)}
            className="flex items-center gap-2 px-3 py-1 text-sm neon-button rounded"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="bg-dark-bg/50">
        <div className="grid grid-cols-2 gap-0">
          {/* Original */}
          <div className="border-r border-dark-border">
            <div className="px-4 py-2 bg-dark-surface/50 border-b border-dark-border">
              <h4 className="text-sm font-medium text-red-400">Original</h4>
            </div>
            <div className="font-mono text-sm">
              {diffLines.map((line, index) => (
                <div
                  key={`left-${index}`}
                  className={`
                    flex px-4 py-1 hover:bg-dark-surface/30 transition-colors
                    ${getLineClass(line.type)}
                  `}
                >
                  {showLineNumbers && (
                    <span className="text-gray-500 text-xs mr-3 w-8 text-right select-none">
                      {line.left ? index + 1 : ''}
                    </span>
                  )}
                  <span className="mr-2">{getTypeIcon(line.type)}</span>
                  <span className="flex-1 whitespace-pre-wrap break-words">
                    {line.left || '\u00A0'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Modified */}
          <div>
            <div className="px-4 py-2 bg-dark-surface/50 border-b border-dark-border">
              <h4 className="text-sm font-medium text-neon-green">Modified</h4>
            </div>
            <div className="font-mono text-sm">
              {diffLines.map((line, index) => (
                <div
                  key={`right-${index}`}
                  className={`
                    flex px-4 py-1 hover:bg-dark-surface/30 transition-colors
                    ${getLineClass(line.type)}
                  `}
                >
                  {showLineNumbers && (
                    <span className="text-gray-500 text-xs mr-3 w-8 text-right select-none">
                      {line.right ? index + 1 : ''}
                    </span>
                  )}
                  <span className="mr-2">{getTypeIcon(line.type)}</span>
                  <span className="flex-1 whitespace-pre-wrap break-words">
                    {line.right || '\u00A0'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex justify-between items-center px-4 py-2 bg-dark-surface/30 border-t border-dark-border text-sm">
        <div className="flex gap-4">
          <span className="text-neon-green">
            +{diffLines.filter(l => l.type === 'add').length} additions
          </span>
          <span className="text-red-400">
            -{diffLines.filter(l => l.type === 'delete').length} deletions
          </span>
          <span className="text-neon-yellow">
            ~{diffLines.filter(l => l.type === 'modify').length} modifications
          </span>
        </div>
        <span className="text-gray-400">
          {diffLines.length} lines total
        </span>
      </div>
    </div>
  )
}
