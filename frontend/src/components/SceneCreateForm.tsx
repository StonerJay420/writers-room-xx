'use client'

import React, { useState } from 'react'
import { X, Save, Plus, Minus } from 'lucide-react'
import { CreateSceneRequest, CreateSceneResponse } from '@/types'
import { api } from '@/lib/api'

interface SceneCreateFormProps {
  isOpen: boolean
  onClose: () => void
  onSceneCreated: (scene: CreateSceneResponse) => void
  defaultChapter?: number
  defaultOrder?: number
}

export function SceneCreateForm({ 
  isOpen, 
  onClose, 
  onSceneCreated, 
  defaultChapter = 1,
  defaultOrder = 1 
}: SceneCreateFormProps) {
  const [formData, setFormData] = useState<CreateSceneRequest>({
    chapter: defaultChapter,
    order_in_chapter: defaultOrder,
    title: '',
    pov: '',
    location: '',
    beats: [''],
    content: '',
    links: {}
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Filter out empty beats
      const filteredBeats = formData.beats?.filter(beat => beat.trim() !== '') || []
      
      const requestData: CreateSceneRequest = {
        ...formData,
        beats: filteredBeats.length > 0 ? filteredBeats : undefined
      }

      const response = await api.post<CreateSceneResponse>('/scenes', requestData)
      onSceneCreated(response)
      onClose()
      
      // Reset form
      setFormData({
        chapter: defaultChapter,
        order_in_chapter: defaultOrder,
        title: '',
        pov: '',
        location: '',
        beats: [''],
        content: '',
        links: {}
      })
    } catch (err: any) {
      setError(err.message || 'Failed to create scene')
    } finally {
      setLoading(false)
    }
  }

  const addBeat = () => {
    setFormData(prev => ({
      ...prev,
      beats: [...(prev.beats || []), '']
    }))
  }

  const removeBeat = (index: number) => {
    setFormData(prev => ({
      ...prev,
      beats: prev.beats?.filter((_, i) => i !== index) || []
    }))
  }

  const updateBeat = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      beats: prev.beats?.map((beat, i) => i === index ? value : beat) || []
    }))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">Create New Scene</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 text-red-300">
              {error}
            </div>
          )}

          {/* Chapter and Scene Order */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Chapter
              </label>
              <input
                type="number"
                min="1"
                value={formData.chapter}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  chapter: parseInt(e.target.value) || 1 
                }))}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Scene Number
              </label>
              <input
                type="number"
                min="1"
                value={formData.order_in_chapter}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  order_in_chapter: parseInt(e.target.value) || 1 
                }))}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
                required
              />
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Scene Title (Optional)
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
              placeholder="A descriptive title for this scene"
            />
          </div>

          {/* POV and Location */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Point of View
              </label>
              <input
                type="text"
                value={formData.pov}
                onChange={(e) => setFormData(prev => ({ ...prev, pov: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
                placeholder="Character name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Location
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
                placeholder="Scene location"
              />
            </div>
          </div>

          {/* Story Beats */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-300">
                Story Beats
              </label>
              <button
                type="button"
                onClick={addBeat}
                className="text-neon-green hover:text-neon-green/80 flex items-center gap-1 text-sm"
              >
                <Plus size={16} />
                Add Beat
              </button>
            </div>
            <div className="space-y-2">
              {formData.beats?.map((beat, index) => (
                <div key={index} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={beat}
                    onChange={(e) => updateBeat(index, e.target.value)}
                    className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
                    placeholder={`Story beat ${index + 1}`}
                  />
                  {(formData.beats?.length || 0) > 1 && (
                    <button
                      type="button"
                      onClick={() => removeBeat(index)}
                      className="text-red-400 hover:text-red-300 p-2"
                    >
                      <Minus size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Content */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Scene Content
            </label>
            <textarea
              value={formData.content}
              onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple resize-none"
              rows={8}
              placeholder="Write your scene content here..."
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-600 rounded-lg text-gray-300 hover:text-white hover:border-gray-500 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-neon-purple rounded-lg text-white hover:bg-neon-purple/80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Save size={16} />
              {loading ? 'Creating...' : 'Create Scene'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}