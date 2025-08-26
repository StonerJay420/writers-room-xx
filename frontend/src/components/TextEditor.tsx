'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { AuthManager } from '@/lib/auth'
import { Wand2, Check, X, Copy, Save, RefreshCw, BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { OpenRouterKeySetup } from './OpenRouterKeySetup'

interface AIRecommendation {
  id: string
  originalText: string
  suggestedText: string
  reason: string
  confidence: number
  type: 'grammar' | 'style' | 'clarity' | 'tone' | 'consistency'
  codexReferences?: string[]
}

interface CodexEntry {
  id: string
  name: string
  type: string
  description: string
  metadata: any
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
  const [hasOpenRouterKey, setHasOpenRouterKey] = useState(false)
  const [checkingKey, setCheckingKey] = useState(true)
  const [codexContext, setCodexContext] = useState<CodexEntry[]>([])
  const [showCodexContext, setShowCodexContext] = useState(false)

  useEffect(() => {
    setHasUnsavedChanges(currentText !== originalText)
  }, [currentText, originalText])

  useEffect(() => {
    checkOpenRouterKey()
  }, [])

  const checkOpenRouterKey = async () => {
    try {
      setCheckingKey(true)
      const hasKey = await AuthManager.hasOpenRouterKey()
      setHasOpenRouterKey(hasKey)
    } catch (error) {
      console.error('Failed to check OpenRouter key:', error)
    } finally {
      setCheckingKey(false)
    }
  }

  const getAIRecommendations = async () => {
    if (!currentText.trim()) return

    if (!hasOpenRouterKey) {
      alert('Please configure your OpenRouter API key first to use AI recommendations.')
      return
    }

    setIsLoadingRecommendations(true)
    try {
      const data = await api.post<{ 
        recommendations?: AIRecommendation[] 
        codexContext?: CodexEntry[]
      }>('/ai/recommendations', {
        text: currentText,
        context: 'manuscript_editing'
      })
      setRecommendations(data.recommendations || [])
      setCodexContext(data.codexContext || [])
      if (data.codexContext && data.codexContext.length > 0) {
        setShowCodexContext(true)
      }
    } catch (error: any) {
      console.error('Failed to get AI recommendations:', error)
      
      if (error.message.includes('401')) {
        alert('Authentication failed. Please check your OpenRouter API key configuration.')
      } else {
        // Mock recommendations for demo purposes when API fails
        setRecommendations([
          {
            id: '1',
            originalText: currentText.split('.')[0] + '.',
            suggestedText: currentText.split('.')[0] + ', creating a vivid scene.',
            reason: 'Enhanced descriptiveness and flow (mock - API failed)',
            confidence: 0.85,
            type: 'style'
          }
        ])
      }
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
      case 'consistency':
        return 'border-orange-400 bg-orange-50'
      default:
        return 'border-gray-400 bg-gray-50'
    }
  }

  if (checkingKey) {
    return (
      <div className="neon-card rounded-lg p-6">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-3 text-neon-cyan" size={32} />
          <p className="text-gray-400">Setting up AI recommendations...</p>
        </div>
      </div>
    )
  }

  if (!hasOpenRouterKey) {
    return (
      <div className="space-y-6">
        <OpenRouterKeySetup onKeyConfigured={() => {
          setHasOpenRouterKey(true)
          checkOpenRouterKey()
        }} />
        
        <div className="neon-card rounded-lg p-6">
          <div className="text-center text-gray-500">
            <Wand2 size={32} className="mx-auto mb-2 opacity-50" />
            <p>Configure your OpenRouter API key above to enable AI-powered text recommendations</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="neon-card rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 sm:p-4 border-b border-dark-border gap-3 sm:gap-0">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <h3 className="font-display font-semibold gradient-text text-base sm:text-lg">
            Text Editor
          </h3>
          {fileName && (
            <span className="text-xs sm:text-sm text-gray-400 truncate">
              {fileName}
            </span>
          )}
          {hasUnsavedChanges && (
            <span className="text-[10px] sm:text-xs text-neon-yellow px-1 sm:px-2 py-0.5 sm:py-1 bg-neon-yellow/10 rounded-full flex-shrink-0">
              Unsaved
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-1 sm:gap-2 w-full sm:w-auto">
          <button
            onClick={getAIRecommendations}
            disabled={isLoadingRecommendations}
            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-2 text-xs sm:text-sm neon-button rounded touch-manipulation flex-1 sm:flex-none justify-center"
          >
            {isLoadingRecommendations ? (
              <RefreshCw size={14} className="animate-spin sm:w-4 sm:h-4" />
            ) : (
              <Wand2 size={14} className="sm:w-4 sm:h-4" />
            )}
            <span className="hidden sm:inline">{isLoadingRecommendations ? 'Getting AI suggestions...' : 'Get AI Suggestions'}</span>
            <span className="sm:hidden">AI</span>
          </button>
          
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-2 text-xs sm:text-sm neon-button rounded touch-manipulation"
          >
            <Copy size={14} className="sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Copy</span>
          </button>
          
          <button
            onClick={handleSave}
            disabled={!hasUnsavedChanges}
            className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-2 text-xs sm:text-sm neon-button rounded disabled:opacity-50 touch-manipulation"
          >
            <Save size={14} className="sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Save</span>
          </button>
        </div>
      </div>

      {/* Main editing area */}
      <div className="flex flex-col lg:flex-row h-64 sm:h-80 lg:h-96">
        {/* Text Editor */}
        <div className="flex-1 border-b lg:border-b-0 lg:border-r border-dark-border">
          <div className="px-3 sm:px-4 py-2 bg-dark-surface/50 border-b border-dark-border">
            <h4 className="text-xs sm:text-sm font-medium text-neon-cyan">Your Text</h4>
          </div>
          <textarea
            value={currentText}
            onChange={(e) => setCurrentText(e.target.value)}
            className="w-full h-full p-3 sm:p-4 bg-transparent text-gray-100 resize-none outline-none font-mono text-xs sm:text-sm leading-relaxed"
            placeholder="Start writing your manuscript here..."
          />
        </div>

        {/* AI Recommendations Panel */}
        <div className="w-full lg:w-80 h-48 lg:h-full flex flex-col">
          <div className="px-3 sm:px-4 py-2 bg-dark-surface/50 border-b border-dark-border">
            <div className="flex items-center justify-between">
              <h4 className="text-xs sm:text-sm font-medium text-neon-green">
                AI Recommendations ({recommendations.length})
              </h4>
              {codexContext.length > 0 && (
                <button
                  onClick={() => setShowCodexContext(!showCodexContext)}
                  className="flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300"
                >
                  <BookOpen size={12} />
                  <span>Codex ({codexContext.length})</span>
                  {showCodexContext ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>
              )}
            </div>
          </div>
          
          {/* Codex Context Panel */}
          {showCodexContext && codexContext.length > 0 && (
            <div className="border-b border-dark-border bg-orange-50/5 max-h-32 overflow-y-auto">
              <div className="p-3 space-y-2">
                <div className="text-xs font-medium text-orange-400 mb-2">
                  Referenced World/Character Information:
                </div>
                {codexContext.map((entry) => (
                  <div key={entry.id} className="text-xs">
                    <span className="font-medium text-orange-300">{entry.name}</span>
                    <span className="text-gray-400 ml-1">({entry.type})</span>
                    {entry.description && (
                      <p className="text-gray-500 mt-1 text-[10px] leading-tight">
                        {entry.description.length > 80 
                          ? `${entry.description.substring(0, 80)}...` 
                          : entry.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="flex-1 overflow-y-auto">
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
                      
                      {rec.codexReferences && rec.codexReferences.length > 0 && (
                        <div>
                          <span className="text-orange-600 font-medium">Codex References:</span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {rec.codexReferences.map((ref, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full"
                              >
                                {ref}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
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