'use client'

import { useState, useEffect } from 'react'
import { BarChart3, FileText, Settings, Upload, Home as HomeIcon, Library } from 'lucide-react'
import { Tabs } from '@/components/Tabs'
import { Dashboard } from '@/components/Dashboard'
import { SceneLibrary } from '@/components/SceneLibrary'
import { AppSettings } from '@/components/AppSettings'
import { FileManager } from '@/components/FileManager'
import { Scene, ModelPreferences } from '@/types'

export default function Home() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [scenes, setScenes] = useState<Scene[]>([])
  const [loading, setLoading] = useState(true)
  const [modelPreferences, setModelPreferences] = useState<ModelPreferences>({
    lore_archivist: 'anthropic/claude-sonnet-4-20250514',
    grim_editor: 'openai/gpt-5',
    tone_metrics: 'anthropic/claude-sonnet-4-20250514',
    supervisor: 'anthropic/claude-sonnet-4-20250514'
  })
  const [processingScene, setProcessingScene] = useState<string | null>(null)

  useEffect(() => {
    loadScenes()
    loadModelPreferences()
  }, [])

  const loadScenes = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/scenes')
      if (response.ok) {
        const data = await response.json()
        setScenes(data)
      }
    } catch (error) {
      console.error('Failed to load scenes:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadModelPreferences = async () => {
    try {
      const response = await fetch('/api/models/preferences')
      if (response.ok) {
        const data = await response.json()
        setModelPreferences(data)
      }
    } catch (error) {
      console.error('Failed to load model preferences:', error)
    }
  }

  const handleIndexFiles = async () => {
    try {
      const response = await fetch('/api/ingest/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paths: ['data/manuscript', 'data/codex'],
          reindex: true
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        alert(`Indexed ${result.scenes} scenes with ${result.chunks} chunks`)
        await loadScenes()
      }
    } catch (error) {
      console.error('Indexing failed:', error)
      alert('Failed to index files')
    }
  }

  const handleModelChange = async (agentName: string, modelId: string) => {
    try {
      const response = await fetch('/api/models/agent-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: agentName,
          llm_model_id: modelId
        })
      })
      
      if (response.ok) {
        setModelPreferences(prev => ({
          ...prev,
          [agentName]: modelId
        }))
      }
    } catch (error) {
      console.error('Failed to update model preference:', error)
    }
  }

  const processScene = async (sceneId: string) => {
    setProcessingScene(sceneId)
    try {
      const response = await fetch('/api/patches/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scene_id: sceneId,
          agents: ['lore_archivist', 'grim_editor'],
          variants: ['safe', 'bold']
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        alert(`Generated ${result.patches?.length || 0} patches. Total cost: $${result.cost_usd?.toFixed(4) || 0}`)
      }
    } catch (error) {
      console.error('Failed to process scene:', error)
      alert('Failed to process scene')
    } finally {
      setProcessingScene(null)
    }
  }

  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <HomeIcon size={16} />,
    },
    {
      id: 'library',
      label: 'Scene Library',
      icon: <Library size={16} />,
      badge: scenes.length
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: <Settings size={16} />,
    },
    {
      id: 'analysis',
      label: 'Analysis',
      icon: <BarChart3 size={16} />,
    },
    {
      id: 'files',
      label: 'File Manager',
      icon: <Upload size={16} />,
    }
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard
            scenes={scenes}
            onProcessScene={processScene}
            processingScene={processingScene}
          />
        )
      case 'library':
        return (
          <SceneLibrary
            scenes={scenes}
            onProcessScene={processScene}
            processingScene={processingScene}
            loading={loading}
          />
        )
      case 'settings':
        return (
          <AppSettings
            modelPreferences={modelPreferences}
            onModelChange={handleModelChange}
          />
        )
      case 'analysis':
        return (
          <div className="text-center py-12 neon-card rounded-lg">
            <BarChart3 size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400">Analysis dashboard coming soon</p>
            <p className="text-gray-500 text-sm">Track your manuscript improvements and metrics</p>
          </div>
        )
      case 'files':
        return (
          <FileManager
            onUploadComplete={loadScenes}
            onIndexFiles={handleIndexFiles}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-6xl font-display font-bold gradient-text animate-glow mb-4">
              Writers Room X
            </h1>
            <p className="text-neon-cyan/60 font-mono text-lg">
              Multi-Agent AI Manuscript Editor
            </p>
            <div className="flex justify-center items-center gap-2 mt-2">
              <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse"></div>
              <p className="text-gray-400 text-sm">
                {scenes.length} scenes loaded
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="neon-card rounded-lg overflow-hidden">
            <Tabs
              tabs={tabs}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />
            
            {/* Tab Content */}
            <div className="p-8">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}