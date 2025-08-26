'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { Wand2, Check, X, Copy, Save, RefreshCw } from 'lucide-react'

interface AIRecommendation {
  id: string
  originalText: string
  suggestedText: string
  reason: string
  confidence: number
  type: 'grammar' | 'style' | 'clarity' | 'tone'
}

interface TextEditorProps {
  initialText?: string
  onSave?: (text: string) => void
  fileName?: string
}

export function TextEditor({ initialText = '', onSave, fileName }: TextEditorProps) {
  const [originalText, setOriginalText] = useState(initialText)
  const [currentText, setCurrentText] = useState(initialText)
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([])
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false)
  const [selectedRecommendation, setSelectedRecommendation] = useState<string | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  useEffect(() => {
    setHasUnsavedChanges(currentText !== originalText)
  }, [currentText, originalText])

  const getAIRecommendations = async () => {
    if (!currentText.trim()) return

    setIsLoadingRecommendations(true)
    try {
      const response = await api.post('/ai/recommendations', {
        text: currentText,
        context: 'manuscript_editing'
      })
      const data = response.data as { recommendations?: AIRecommendation[] }
      setRecommendations(data.recommendations || [])
    } catch (error) {
      console.error('Failed to get AI recommendations:', error)
      // Mock recommendations for demo purposes
      setRecommendations([
        {
          id: '1',
          originalText: currentText.split('.')[0] + '.',
          suggestedText: currentText.split('.')[0] + ', creating a vivid scene.',
          reason: 'Enhanced descriptiveness and flow',
          confidence: 0.85,
          type: 'style'
        }
      ])
    } finally {
      setIsLoadingRecommendations(false)
    }
  }

  const applyRecommendation = (recommendation: AIRecommendation) => {
    const newText = currentText.replace(
      recommendation.originalText,
      recommendation.suggestedText
    )
    setCurrentText(newText)
    setRecommendations(prev => prev.filter(r => r.id !== recommendation.id))
  }

  const rejectRecommendation = (recommendationId: string) => {
    setRecommendations(prev => prev.filter(r => r.id !== recommendationId))
  }

  const handleSave = () => {
    if (onSave) {
      onSave(currentText)
    }
    setOriginalText(currentText)
    setHasUnsavedChanges(false)
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(currentText)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  const getRecommendationColor = (type: AIRecommendation['type']) => {
    switch (type) {
      case 'grammar':
        return 'border-red-400 bg-red-50'
      case 'style':
        return 'border-blue-400 bg-blue-50'
      case 'clarity':
        return 'border-yellow-400 bg-yellow-50'
      case 'tone':
        return 'border-purple-400 bg-purple-50'
      default:
        return 'border-gray-400 bg-gray-50'
    }
  }

  return (
    <div className="neon-card rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-border">
        <div className="flex items-center gap-3">
          <h3 className="font-display font-semibold gradient-text">
            Text Editor
          </h3>
          {fileName && (
            <span className="text-sm text-gray-400">
              {fileName}
            </span>
          )}
          {hasUnsavedChanges && (
            <span className="text-xs text-neon-yellow px-2 py-1 bg-neon-yellow/10 rounded-full">
              Unsaved changes
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={getAIRecommendations}
            disabled={isLoadingRecommendations}
            className="flex items-center gap-2 px-3 py-1 text-sm neon-button rounded"
          >
            {isLoadingRecommendations ? (
              <RefreshCw size={16} className="animate-spin" />
            ) : (
              <Wand2 size={16} />
            )}
            {isLoadingRecommendations ? 'Getting AI suggestions...' : 'Get AI Suggestions'}
          </button>
          
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-2 px-3 py-1 text-sm neon-button rounded"
          >
            <Copy size={16} />
            Copy
          </button>
          
          <button
            onClick={handleSave}
            disabled={!hasUnsavedChanges}
            className="flex items-center gap-2 px-3 py-1 text-sm neon-button rounded disabled:opacity-50"
          >
            <Save size={16} />
            Save
          </button>
        </div>
      </div>

      {/* Main editing area */}
      <div className="flex h-96">
        {/* Text Editor */}
        <div className="flex-1 border-r border-dark-border">
          <div className="px-4 py-2 bg-dark-surface/50 border-b border-dark-border">
            <h4 className="text-sm font-medium text-neon-cyan">Your Text</h4>
          </div>
          <textarea
            value={currentText}
            onChange={(e) => setCurrentText(e.target.value)}
            className="w-full h-full p-4 bg-transparent text-gray-100 resize-none outline-none font-mono text-sm leading-relaxed"
            placeholder="Start writing your manuscript here..."
          />
        </div>

        {/* AI Recommendations Panel */}
        <div className="w-80">
          <div className="px-4 py-2 bg-dark-surface/50 border-b border-dark-border">
            <h4 className="text-sm font-medium text-neon-green">
              AI Recommendations ({recommendations.length})
            </h4>
          </div>
          
          <div className="h-full overflow-y-auto">
            {recommendations.length === 0 ? (
              <div className="p-4 text-center text-gray-400">
                <Wand2 size={32} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  Click "Get AI Suggestions" to see recommendations for improving your text
                </p>
              </div>
            ) : (
              <div className="space-y-3 p-4">
                {recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className={`
                      border-2 rounded-lg p-3 transition-all duration-200
                      ${getRecommendationColor(rec.type)}
                      ${selectedRecommendation === rec.id ? 'ring-2 ring-neon-purple' : ''}
                    `}
                    onClick={() => setSelectedRecommendation(
                      selectedRecommendation === rec.id ? null : rec.id
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs font-medium uppercase tracking-wide text-gray-600">
                        {rec.type}
                      </span>
                      <div className="flex gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            applyRecommendation(rec)
                          }}
                          className="p-1 text-green-600 hover:bg-green-600/20 rounded"
                        >
                          <Check size={14} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            rejectRecommendation(rec.id)
                          }}
                          className="p-1 text-red-600 hover:bg-red-600/20 rounded"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-red-600 font-medium">Original:</span>
                        <p className="mt-1 text-gray-700 italic">"{rec.originalText}"</p>
                      </div>
                      
                      <div>
                        <span className="text-green-600 font-medium">Suggested:</span>
                        <p className="mt-1 text-gray-700 italic">"{rec.suggestedText}"</p>
                      </div>
                      
                      <div>
                        <span className="text-gray-600 font-medium">Reason:</span>
                        <p className="mt-1 text-gray-600">{rec.reason}</p>
                      </div>
                      
                      <div className="flex justify-between items-center text-xs text-gray-500">
                        <span>Confidence: {Math.round(rec.confidence * 100)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex justify-between items-center px-4 py-2 bg-dark-surface/30 border-t border-dark-border text-sm">
        <div className="flex gap-4">
          <span className="text-gray-400">
            Words: {currentText.split(/\s+/).filter(w => w.length > 0).length}
          </span>
          <span className="text-gray-400">
            Characters: {currentText.length}
          </span>
        </div>
        <div className="flex gap-4">
          <span className="text-neon-green">
            {recommendations.length} AI suggestions available
          </span>
        </div>
      </div>
    </div>
  )
}