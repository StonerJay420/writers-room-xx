'use client'

import { useState, useEffect } from 'react'
import { Key, Lock, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react'
import { AuthManager } from '@/lib/auth'

interface OpenRouterKeySetupProps {
  onKeyConfigured?: () => void
}

export function OpenRouterKeySetup({ onKeyConfigured }: OpenRouterKeySetupProps) {
  const [openRouterKey, setOpenRouterKey] = useState('')
  const [hasKey, setHasKey] = useState(false)
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showKeyInput, setShowKeyInput] = useState(false)

  useEffect(() => {
    checkKeyStatus()
  }, [])

  const checkKeyStatus = async () => {
    try {
      setChecking(true)
      const configured = await AuthManager.hasOpenRouterKey()
      setHasKey(configured)
    } catch (error) {
      console.error('Failed to check key status:', error)
    } finally {
      setChecking(false)
    }
  }

  const handleSaveKey = async () => {
    if (!openRouterKey.trim()) {
      setError('Please enter your OpenRouter API key')
      return
    }

    if (!openRouterKey.startsWith('sk-') && !openRouterKey.startsWith('or-')) {
      setError('Invalid OpenRouter API key format. Keys should start with "sk-" or "or-"')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await AuthManager.setOpenRouterKey(openRouterKey)
      setHasKey(true)
      setShowKeyInput(false)
      setOpenRouterKey('')
      if (onKeyConfigured) onKeyConfigured()
    } catch (error: any) {
      setError(error.message || 'Failed to save OpenRouter key')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveKey = async () => {
    setLoading(true)
    try {
      await AuthManager.removeOpenRouterKey()
      setHasKey(false)
      setShowKeyInput(false)
    } catch (error) {
      setError('Failed to remove OpenRouter key')
    } finally {
      setLoading(false)
    }
  }

  if (checking) {
    return (
      <div className="neon-card rounded-lg p-6">
        <div className="flex items-center gap-3">
          <Key className="text-neon-cyan animate-pulse" size={24} />
          <div>
            <h3 className="font-display font-semibold text-neon-cyan">Checking OpenRouter Setup...</h3>
            <p className="text-gray-400 text-sm">Verifying your API key configuration</p>
          </div>
        </div>
      </div>
    )
  }

  if (hasKey && !showKeyInput) {
    return (
      <div className="neon-card rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle className="text-neon-green" size={24} />
            <div>
              <h3 className="font-display font-semibold text-neon-green">OpenRouter Connected</h3>
              <p className="text-gray-400 text-sm">Your API key is configured and ready for AI recommendations</p>
            </div>
          </div>
          <button
            onClick={() => setShowKeyInput(true)}
            className="px-4 py-2 text-sm neon-button rounded border border-neon-purple/30"
          >
            Update Key
          </button>
        </div>
        
        {showKeyInput && (
          <div className="mt-4 pt-4 border-t border-dark-border">
            <button
              onClick={handleRemoveKey}
              disabled={loading}
              className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded disabled:opacity-50"
            >
              {loading ? 'Removing...' : 'Remove Key'}
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="neon-card rounded-lg p-6">
      <div className="flex items-start gap-3 mb-4">
        <AlertCircle className="text-neon-yellow mt-1" size={24} />
        <div>
          <h3 className="font-display font-semibold text-neon-yellow mb-2">OpenRouter API Key Required</h3>
          <p className="text-gray-300 text-sm mb-3">
            To use AI-powered text recommendations, you need to provide your own OpenRouter API key. 
            This enables the BYOK (Bring Your Own Key) feature for cost control and privacy.
          </p>
          
          <div className="flex items-center gap-2 text-sm text-neon-cyan">
            <ExternalLink size={16} />
            <a 
              href="https://openrouter.ai/keys" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:underline"
            >
              Get your OpenRouter API key here
            </a>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            OpenRouter API Key
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-3 text-gray-400" size={16} />
            <input
              type="password"
              value={openRouterKey}
              onChange={(e) => setOpenRouterKey(e.target.value)}
              placeholder="sk-or-v1-..."
              className="w-full pl-10 pr-4 py-2 bg-dark-surface border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:border-neon-cyan focus:outline-none"
            />
          </div>
          <p className="mt-1 text-xs text-gray-500">
            Your key is stored securely and only used for your AI requests
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleSaveKey}
            disabled={loading || !openRouterKey.trim()}
            className="flex-1 px-4 py-2 neon-button rounded disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save API Key'}
          </button>
          
          {hasKey && (
            <button
              onClick={() => setShowKeyInput(false)}
              className="px-4 py-2 border border-gray-600 text-gray-300 rounded hover:bg-gray-700"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}