'use client'

import { useState, useEffect } from 'react'
import { Scene } from '@/types'
import { api } from '@/lib/api'
import Link from 'next/link'
import { FileUpload } from '@/components/FileUpload'
import { BookOpen, ChevronRight, Upload } from 'lucide-react'

export default function Home() {
  const [scenes, setScenes] = useState<Scene[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    loadScenes()
  }, [selectedChapter, searchTerm])

  const loadScenes = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (selectedChapter) params.append('chapter', selectedChapter.toString())
      if (searchTerm) params.append('search', searchTerm)
      
      const scenesData = await api.get(`/scenes?${params}`)
      setScenes(scenesData)
    } catch (error) {
      console.error('Failed to load scenes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleIndexFiles = async () => {
    try {
      const result = await api.post('/ingest/index', {
        paths: ['data/manuscript', 'data/codex'],
        reindex: true
      })
      
      alert(`Indexed ${result.scenes} scenes and ${result.codex_files} codex files`)
      loadScenes()
    } catch (error) {
      console.error('Indexing failed:', error)
      alert('Failed to index files')
    }
  }

  const chapters = [...new Set(scenes.map(s => s.chapter))].sort()

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Manuscript Scenes</h1>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Upload size={16} />
            <span>Upload Files</span>
          </button>
          <button
            onClick={handleIndexFiles}
            className="btn btn-primary"
          >
            Index Files
          </button>
        </div>
      </div>

      {/* Upload Component */}
      {showUpload && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Upload Files</h2>
          <FileUpload onUploadComplete={() => {
            loadScenes()
            setShowUpload(false)
          }} />
        </div>
      )}

      {/* Filters */}
      <div className="card p-4">
        <div className="flex space-x-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Chapter
            </label>
            <select
              value={selectedChapter || ''}
              onChange={(e) => setSelectedChapter(e.target.value ? parseInt(e.target.value) : null)}
              className="border border-gray-300 rounded-md px-3 py-1"
            >
              <option value="">All Chapters</option>
              {chapters.map(ch => (
                <option key={ch} value={ch}>Chapter {ch}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search scenes..."
              className="w-full border border-gray-300 rounded-md px-3 py-1"
            />
          </div>
        </div>
      </div>

      {/* Scenes List */}
      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-600">Loading scenes...</p>
        </div>
      ) : scenes.length === 0 ? (
        <div className="text-center py-8">
          <BookOpen size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">No scenes found. Upload some manuscript files to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {scenes.map((scene) => (
            <Link key={scene.id} href={`/scenes/${scene.id}`}>
              <div className="card p-4 hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {scene.id}
                      </h3>
                      <span className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full">
                        Chapter {scene.chapter}
                      </span>
                    </div>
                    <div className="mt-2 space-y-1">
                      <p className="text-sm text-gray-600">
                        POV: {scene.pov} • Location: {scene.location}
                      </p>
                      <p className="text-sm text-gray-500">
                        {scene.word_count} words • Last updated: {new Date(scene.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <ChevronRight size={20} className="text-gray-400" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
