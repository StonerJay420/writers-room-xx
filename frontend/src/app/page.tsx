'use client'

import { useState, useEffect } from 'react'
import { BarChart3, FileText, Settings, Upload, Home as HomeIcon, Library, BookOpen, Package, Edit } from 'lucide-react'
import { Tabs } from '@/components/Tabs'
import { Dashboard } from '@/components/Dashboard'
import { SceneLibrary } from '@/components/SceneLibrary'
import { AppSettings } from '@/components/AppSettings'
import { FileManager } from '@/components/FileManager'
import { ManuscriptNavigator } from '@/components/ManuscriptNavigator'
import { CodexManager } from '@/components/CodexManager'
import { SceneCreateForm } from '@/components/SceneCreateForm'
import { TextEditor } from '@/components/TextEditor'
import { Scene, ModelPreferences, CreateSceneResponse } from '@/types'

export default function Home() {
  const [activeTab, setActiveTab] = useState('navigator')
  const [scenes, setScenes] = useState<Scene[]>([])
  const [loading, setLoading] = useState(true)
  const [modelPreferences, setModelPreferences] = useState<ModelPreferences>({
    lore_archivist: 'anthropic/claude-sonnet-4-20250514',
    grim_editor: 'openai/gpt-5',
    tone_metrics: 'anthropic/claude-sonnet-4-20250514',
    supervisor: 'anthropic/claude-sonnet-4-20250514'
  })
  const [processingScene, setProcessingScene] = useState<string | null>(null)
  const [showSceneCreateForm, setShowSceneCreateForm] = useState(false)
  const [selectedScene, setSelectedScene] = useState<Scene | null>(null)
  const [sceneCreateDefaults, setSceneCreateDefaults] = useState({ chapter: 1, order: 1 })

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

  const handleCreateScene = (chapter: number, order: number) => {
    setSceneCreateDefaults({ chapter, order })
    setShowSceneCreateForm(true)
  }

  const handleSceneCreated = async (scene: CreateSceneResponse) => {
    await loadScenes()
    setShowSceneCreateForm(false)
    // Optionally switch to the scene library to see the new scene
    setActiveTab('library')
  }

  const handleSceneSelect = (scene: Scene) => {
    setSelectedScene(scene)
    // Navigate to scene detail or show scene content
    console.log('Selected scene:', scene)
  }

  const openSceneInEditor = (scene: Scene) => {
    setSelectedScene(scene)
    setActiveTab('editor')
  }

  const tabs = [
    {
      id: 'navigator',
      label: 'Navigator',
      icon: <BookOpen size={16} />,
      badge: scenes.length
    },
    {
      id: 'editor',
      label: 'AI Editor',
      icon: <Edit size={16} />,
    },
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
      id: 'codex',
      label: 'Codex',
      icon: <Package size={16} />,
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
      case 'navigator':
        return (
          <div className="h-[800px] flex">
            <div className="w-80 border-r border-gray-700">
              <ManuscriptNavigator
                scenes={scenes}
                onSceneSelect={handleSceneSelect}
                onCreateScene={handleCreateScene}
                selectedSceneId={selectedScene?.id}
              />
            </div>
            <div className="flex-1 p-6">
              {selectedScene ? (
                <div className="neon-card rounded-lg p-6">
                  <h2 className="text-xl font-semibold text-white mb-4">
                    Scene {selectedScene.id}
                  </h2>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <span className="text-gray-400">Chapter:</span>
                      <span className="ml-2 text-white">{selectedScene.chapter}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Scene:</span>
                      <span className="ml-2 text-white">{selectedScene.order_in_chapter}</span>
                    </div>
                    {selectedScene.pov && (
                      <div>
                        <span className="text-gray-400">POV:</span>
                        <span className="ml-2 text-neon-cyan">{selectedScene.pov}</span>
                      </div>
                    )}
                    {selectedScene.location && (
                      <div>
                        <span className="text-gray-400">Location:</span>
                        <span className="ml-2 text-neon-green">{selectedScene.location}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => processScene(selectedScene.id)}
                      disabled={processingScene === selectedScene.id}
                      className="bg-neon-purple hover:bg-neon-purple/80 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                    >
                      {processingScene === selectedScene.id ? 'Processing...' : 'Process Scene'}
                    </button>
                    <button
                      onClick={() => openSceneInEditor(selectedScene)}
                      className="bg-neon-cyan hover:bg-neon-cyan/80 text-white px-4 py-2 rounded-lg"
                    >
                      <Edit size={16} className="inline mr-2" />
                      Edit with AI
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-20 text-gray-400">
                  <BookOpen size={64} className="mx-auto mb-4 opacity-50" />
                  <p className="text-lg mb-2">Select a scene to view details</p>
                  <p className="text-sm">Or create a new scene using the navigator</p>
                </div>
              )}
            </div>
          </div>
        )
      case 'editor':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-display font-bold gradient-text mb-2">
                AI-Powered Text Editor
              </h2>
              <p className="text-gray-400">
                Write and improve your manuscript with AI assistance
              </p>
            </div>
            <TextEditor
              initialText={selectedScene ? `# Scene ${selectedScene.id}\n\nChapter ${selectedScene.chapter}, Scene ${selectedScene.order_in_chapter}\n\n[Scene content goes here...]` : ''}
              onSave={async (text) => {
                if (selectedScene) {
                  console.log('Saving scene content for:', selectedScene.id, text)
                  // You could implement a scene content update endpoint here
                }
              }}
              fileName={selectedScene ? `${selectedScene.id}.md` : undefined}
            />
          </div>
        )
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
      case 'codex':
        return (
          <CodexManager
            onItemCreated={(item) => {
              console.log('Created codex item:', item)
              // Optionally trigger indexing or other actions
            }}
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
      
      {/* Scene Creation Modal */}
      <SceneCreateForm
        isOpen={showSceneCreateForm}
        onClose={() => setShowSceneCreateForm(false)}
        onSceneCreated={handleSceneCreated}
        defaultChapter={sceneCreateDefaults.chapter}
        defaultOrder={sceneCreateDefaults.order}
      />
    </div>
  )
}