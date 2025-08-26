'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, Sparkles, Info } from 'lucide-react'

interface Model {
  id: string
  name: string
  description?: string
  context_length?: number
  pricing?: {
    prompt: number
    completion: number
  }
  provider: string
  modalities: string[]
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
      const response = await fetch('/api/models/available')
      if (response.ok) {
        const data: Model[] = await response.json()
        setModels(data)
      } else {
        console.error('Failed to fetch models:', response.status, response.statusText)
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
    if (price < 0.001) {
      return `$${(price * 1000000).toFixed(2)}/1M`
    }
    return `$${(price * 1000).toFixed(3)}/1K`
  }

  const getProviderColor = (provider: string) => {
    const colors = {
      anthropic: 'text-neon-purple',
      openai: 'text-neon-green',
      google: 'text-neon-yellow',
      xai: 'text-neon-pink',
      meta: 'text-neon-cyan',
      mistral: 'text-orange-400'
    }
    return colors[provider as keyof typeof colors] || 'text-gray-400'
  }

  const groupedModels = models.reduce((acc, model) => {
    if (!acc[model.provider]) {
      acc[model.provider] = []
    }
    acc[model.provider].push(model)
    return acc
  }, {} as Record<string, Model[]>)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-2 neon-input rounded-lg transition-colors"
        disabled={loading}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-neon-purple" />
          <span className="text-sm text-gray-200">
            {loading ? 'Loading models...' : getSelectedModelName()}
          </span>
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-[99999] w-full mt-2 neon-card rounded-lg shadow-xl max-h-96 overflow-y-auto">
          {Object.entries(groupedModels).map(([provider, providerModels]) => (
            <div key={provider} className="border-b border-dark-border last:border-b-0">
              <div className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider bg-dark-surface/50 ${getProviderColor(provider)}`}>
                {provider}
              </div>
              {providerModels.map((model) => (
                <button
                  key={model.id}
                  onClick={() => handleModelSelect(model.id)}
                  className={`w-full px-4 py-3 text-left hover:bg-neon-purple/10 transition-colors border-b border-dark-border/50 last:border-b-0 ${
                    selectedModel === model.id ? 'bg-neon-purple/20' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-200 mb-1">{model.name}</div>
                      {model.description && (
                        <div className="text-xs text-gray-400 mb-2">{model.description}</div>
                      )}
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        {model.context_length && (
                          <span>Context: {(model.context_length / 1000).toFixed(0)}K</span>
                        )}
                        {model.modalities.length > 1 && (
                          <span className="text-neon-cyan">Multimodal</span>
                        )}
                      </div>
                    </div>
                    {model.pricing && (
                      <div className="text-xs text-gray-500 ml-4 text-right">
                        <div>In: {formatPrice(model.pricing.prompt)}</div>
                        <div>Out: {formatPrice(model.pricing.completion)}</div>
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}