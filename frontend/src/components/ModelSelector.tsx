'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, Sparkles, Info } from 'lucide-react'

interface Model {
  id: string
  name: string
  description?: string
  pricing?: {
    prompt: number
    completion: number
  }
}

interface ModelSelectorProps {
  agentName: string
  currentModel?: string
  onModelChange: (agentName: string, modelId: string) => void
}

export function ModelSelector({ agentName, currentModel, onModelChange }: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([])
  const [selectedModel, setSelectedModel] = useState(currentModel || '')
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchModels()
  }, [])

  useEffect(() => {
    if (currentModel) {
      setSelectedModel(currentModel)
    }
  }, [currentModel])

  const fetchModels = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/models/available')
      if (response.ok) {
        const data = await response.json()
        setModels(data)
      }
    } catch (error) {
      console.error('Failed to fetch models:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId)
    onModelChange(agentName, modelId)
    setIsOpen(false)
  }

  const getSelectedModelName = () => {
    const model = models.find(m => m.id === selectedModel)
    return model?.name || selectedModel || 'Select Model'
  }

  const formatPrice = (price?: number) => {
    if (!price) return ''
    return `$${(price * 1000).toFixed(3)}/1K`
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-750 transition-colors"
        disabled={loading}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span className="text-sm text-gray-200">{getSelectedModelName()}</span>
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-96 overflow-y-auto">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => handleModelSelect(model.id)}
              className={`w-full px-4 py-3 text-left hover:bg-gray-750 transition-colors border-b border-gray-700 last:border-b-0 ${
                selectedModel === model.id ? 'bg-gray-750' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="font-medium text-gray-200">{model.name}</div>
                  {model.description && (
                    <div className="text-xs text-gray-400 mt-1">{model.description}</div>
                  )}
                </div>
                {model.pricing && (
                  <div className="text-xs text-gray-500 ml-4">
                    <div>Input: {formatPrice(model.pricing.prompt)}</div>
                    <div>Output: {formatPrice(model.pricing.completion)}</div>
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}