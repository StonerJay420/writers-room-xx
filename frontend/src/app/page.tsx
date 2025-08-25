'use client'

import { useState, useEffect } from 'react'
import { FileUpload } from '@/components/FileUpload'
import { ModelSelector } from '@/components/ModelSelector'
import { BookOpen, ChevronRight, Upload, Settings, Zap, FileText, Brain } from 'lucide-react'

interface Scene {
  id: string
  chapter: number
  order_in_chapter: number
  pov?: string
  location?: string
  beats_json?: any
  links_json?: any
}

interface ModelPreferences {
  lore_archivist: string
  grim_editor: string
  tone_metrics: string
  supervisor: string
}

export default function Home() {
  const [scenes, setScenes] = useState<Scene[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [modelPreferences, setModelPreferences] = useState<ModelPreferences>({
    lore_archivist: 'anthropic/claude-3-opus',
    grim_editor: 'openai/gpt-4-turbo-preview',
    tone_metrics: 'anthropic/claude-3-sonnet',
    supervisor: 'anthropic/claude-3-opus'
  })
  const [processingScene, setProcessingScene] = useState<string | null>(null)

  useEffect(() => {
    loadScenes()
    loadModelPreferences()
  }, [selectedChapter, searchTerm])

  const loadScenes = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (selectedChapter) params.append('chapter', selectedChapter.toString())
      if (searchTerm) params.append('search', searchTerm)
      
      const response = await fetch(`http://localhost:8000/api/scenes?${params}`)
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
      const response = await fetch('http://localhost:8000/api/models/preferences')
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
      const response = await fetch('http://localhost:8000/api/ingest/index', {
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
        loadScenes()
      }
    } catch (error) {
      console.error('Indexing failed:', error)
      alert('Failed to index files')
    }
  }

  const handleModelChange = async (agentName: string, modelId: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/models/agent-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: agentName,
          model_id: modelId
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
      const response = await fetch('http://localhost:8000/api/patches/generate', {
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
        alert(`Generated ${result.patches.length} patches. Total cost: $${result.cost_usd.toFixed(4)}`)
      }
    } catch (error) {
      console.error('Failed to process scene:', error)
      alert('Failed to process scene')
    } finally {
      setProcessingScene(null)
    }
  }

  const chapters = [...new Set(scenes.map(s => s.chapter))].sort((a, b) => a - b)

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-5xl font-display font-bold gradient-text animate-glow">
                Writers Room X
              </h1>
              <p className="text-neon-cyan/60 mt-2 font-mono text-sm">Multi-Agent AI Manuscript Editor</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="neon-button rounded-lg flex items-center space-x-2"
              >
                <Settings size={16} />
                <span>Agent Models</span>
              </button>
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="neon-button rounded-lg flex items-center space-x-2"
              >
                <Upload size={16} />
                <span>Upload</span>
              </button>
              <button
                onClick={handleIndexFiles}
                className="px-4 py-2 bg-gradient-to-r from-neon-purple to-neon-pink hover:from-neon-pink hover:to-neon-purple rounded-lg transition-all duration-300 shadow-neon-purple"
              >
                Index Files
              </button>
            </div>
          </div>

          {/* Model Settings */}
          {showSettings && (
            <div className="neon-card rounded-lg p-6 hologram-effect">
              <h2 className="text-xl font-display font-semibold mb-4 flex items-center gap-2 neon-text">
                <Brain className="w-5 h-5 text-neon-purple" />
                Agent Model Configuration
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Lore Archivist
                  </label>
                  <ModelSelector
                    agentName="lore_archivist"
                    currentModel={modelPreferences.lore_archivist}
                    onModelChange={handleModelChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Grim Editor
                  </label>
                  <ModelSelector
                    agentName="grim_editor"
                    currentModel={modelPreferences.grim_editor}
                    onModelChange={handleModelChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Tone Metrics
                  </label>
                  <ModelSelector
                    agentName="tone_metrics"
                    currentModel={modelPreferences.tone_metrics}
                    onModelChange={handleModelChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Supervisor
                  </label>
                  <ModelSelector
                    agentName="supervisor"
                    currentModel={modelPreferences.supervisor}
                    onModelChange={handleModelChange}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Upload Component */}
          {showUpload && (
            <div className="neon-card rounded-lg p-6">
              <h2 className="text-lg font-display font-semibold mb-4 neon-text">Upload Files</h2>
              <FileUpload onUploadComplete={() => {
                loadScenes()
                setShowUpload(false)
              }} />
            </div>
          )}

          {/* Filters */}
          <div className="neon-card rounded-lg p-4">
            <div className="flex space-x-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Filter by Chapter
                </label>
                <select
                  value={selectedChapter || ''}
                  onChange={(e) => setSelectedChapter(e.target.value ? parseInt(e.target.value) : null)}
                  className="neon-input rounded-md px-3 py-1"
                >
                  <option value="">All Chapters</option>
                  {chapters.map(ch => (
                    <option key={ch} value={ch}>Chapter {ch}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Search
                </label>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search scenes..."
                  className="w-full neon-input rounded-md px-3 py-1 placeholder-gray-500"
                />
              </div>
            </div>
          </div>

          {/* Scenes List */}
          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
              <p className="mt-2 text-gray-400">Loading scenes...</p>
            </div>
          ) : scenes.length === 0 ? (
            <div className="text-center py-12 bg-gray-800 border border-gray-700 rounded-lg">
              <BookOpen size={48} className="mx-auto text-gray-600 mb-4" />
              <p className="text-gray-400">No scenes found. Upload manuscript files to get started.</p>
              <p className="text-gray-500 text-sm mt-2">Place .md files in data/manuscript/ and click "Index Files"</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {scenes.map((scene) => (
                <div key={scene.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-purple-600 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-semibold text-gray-100">
                          {scene.id}
                        </h3>
                        <span className="px-2 py-1 bg-purple-900 text-purple-300 text-xs rounded-full">
                          Chapter {scene.chapter}
                        </span>
                      </div>
                      <div className="mt-2 space-y-1">
                        {scene.pov && (
                          <p className="text-sm text-gray-400">
                            POV: {scene.pov} {scene.location && `• Location: ${scene.location}`}
                          </p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => processScene(scene.id)}
                      disabled={processingScene === scene.id}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {processingScene === scene.id ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <Zap size={16} />
                          <span>Process</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}