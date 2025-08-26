'use client'

import { useState } from 'react'
import { BookOpen, Search, Filter, Grid, List, ChevronDown } from 'lucide-react'
import { SceneCard } from './SceneCard'
import { Scene } from '@/types'

interface SceneLibraryProps {
  scenes: Scene[]
  onProcessScene: (sceneId: string) => void
  processingScene: string | null
  loading: boolean
}

export function SceneLibrary({ scenes, onProcessScene, processingScene, loading }: SceneLibraryProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null)
  const [sortBy, setSortBy] = useState('chapter')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showFilters, setShowFilters] = useState(false)

  const chapters = [...new Set(scenes.map(s => s.chapter))].sort((a, b) => a - b)
  
  const filteredScenes = scenes
    .filter(scene => {
      const matchesSearch = !searchTerm || 
        scene.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        scene.pov?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        scene.location?.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesChapter = !selectedChapter || scene.chapter === selectedChapter
      
      return matchesSearch && matchesChapter
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'chapter':
          return a.chapter - b.chapter || a.order_in_chapter - b.order_in_chapter
        case 'pov':
          return (a.pov || '').localeCompare(b.pov || '')
        case 'location':
          return (a.location || '').localeCompare(b.location || '')
        default:
          return 0
      }
    })

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neon-purple mb-4"></div>
        <p className="text-gray-400">Loading scenes...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Search and Controls */}
      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search scenes by ID, POV, or location..."
              className="w-full neon-input rounded-lg pl-10 pr-4 py-3"
            />
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`neon-button rounded-lg px-4 py-2 flex items-center gap-2 ${
              showFilters ? 'bg-neon-purple/20' : ''
            }`}
          >
            <Filter size={16} />
            Filters
          </button>
          
          <div className="flex bg-dark-surface/50 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-neon-purple/20 text-neon-purple' : 'text-gray-400'}`}
            >
              <Grid size={16} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-neon-purple/20 text-neon-purple' : 'text-gray-400'}`}
            >
              <List size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="neon-card rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Chapter
              </label>
              <select
                value={selectedChapter || ''}
                onChange={(e) => setSelectedChapter(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full neon-input rounded-md px-3 py-2"
              >
                <option value="">All Chapters</option>
                {chapters.map(ch => (
                  <option key={ch} value={ch}>Chapter {ch}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full neon-input rounded-md px-3 py-2"
              >
                <option value="chapter">Chapter Order</option>
                <option value="pov">Point of View</option>
                <option value="location">Location</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={() => {
                  setSearchTerm('')
                  setSelectedChapter(null)
                  setSortBy('chapter')
                }}
                className="neon-button rounded-lg px-4 py-2"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Scene Count */}
      <div className="flex items-center justify-between">
        <p className="text-gray-400">
          Showing {filteredScenes.length} of {scenes.length} scenes
        </p>
        {selectedChapter && (
          <span className="px-3 py-1 bg-neon-purple/20 text-neon-purple rounded-full text-sm">
            Chapter {selectedChapter}
          </span>
        )}
      </div>

      {/* Scenes Grid/List */}
      {filteredScenes.length === 0 ? (
        <div className="text-center py-12 neon-card rounded-lg">
          <BookOpen size={48} className="mx-auto text-gray-600 mb-4" />
          <p className="text-gray-400 mb-2">
            {searchTerm || selectedChapter ? 'No scenes match your filters' : 'No scenes found'}
          </p>
          <p className="text-gray-500 text-sm">
            {!searchTerm && !selectedChapter && 'Upload manuscript files to get started'}
          </p>
        </div>
      ) : (
        <div className={`
          ${viewMode === 'grid' 
            ? 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6' 
            : 'space-y-4'
          }
        `}>
          {filteredScenes.map((scene) => (
            <SceneCard
              key={scene.id}
              scene={scene}
              onProcess={onProcessScene}
              isProcessing={processingScene === scene.id}
              compact={viewMode === 'list'}
            />
          ))}
        </div>
      )}
    </div>
  )
}