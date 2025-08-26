'use client'

import React, { useState, useEffect } from 'react'
import { Plus, Search, User, MapPin, Package, Building, Calendar, Edit, Trash2, Save, X } from 'lucide-react'
import { CodexItem, Character, Location, CreateCodexItemRequest, CreateCodexItemResponse } from '@/types'
import { api } from '@/lib/api'

interface CodexManagerProps {
  onItemCreated?: (item: CreateCodexItemResponse) => void
}

export function CodexManager({ onItemCreated }: CodexManagerProps) {
  const [items, setItems] = useState<CodexItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedType, setSelectedType] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingItem, setEditingItem] = useState<string | null>(null)

  const itemTypes = [
    { id: 'all', label: 'All Items', icon: Package },
    { id: 'character', label: 'Characters', icon: User },
    { id: 'location', label: 'Locations', icon: MapPin },
    { id: 'organization', label: 'Organizations', icon: Building },
    { id: 'event', label: 'Events', icon: Calendar },
    { id: 'object', label: 'Objects', icon: Package }
  ]

  useEffect(() => {
    loadItems()
  }, [selectedType])

  const loadItems = async () => {
    try {
      setLoading(true)
      const typeParam = selectedType === 'all' ? '' : selectedType
      const response = await api.get<CodexItem[]>(`/codex/items?item_type=${typeParam}&search=${searchTerm}`)
      setItems(response)
    } catch (error) {
      console.error('Failed to load codex items:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredItems = items.filter(item => {
    const matchesSearch = !searchTerm || 
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesType = selectedType === 'all' || item.type === selectedType
    
    return matchesSearch && matchesType
  })

  const getTypeIcon = (type: string) => {
    const typeConfig = itemTypes.find(t => t.id === type)
    return typeConfig?.icon || Package
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      character: 'text-neon-cyan',
      location: 'text-neon-green',
      organization: 'text-neon-purple',
      event: 'text-neon-pink',
      object: 'text-neon-yellow'
    }
    return colors[type] || 'text-gray-400'
  }

  return (
    <div className="h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Codex Manager</h2>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-neon-purple hover:bg-neon-purple/80 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus size={16} />
            Create Item
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search codex items..."
            className="w-full bg-gray-800 border border-gray-600 rounded-lg pl-10 pr-4 py-3 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
          />
        </div>

        {/* Type Filter */}
        <div className="flex gap-2 overflow-x-auto">
          {itemTypes.map(type => {
            const IconComponent = type.icon
            return (
              <button
                key={type.id}
                onClick={() => setSelectedType(type.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                  selectedType === type.id
                    ? 'bg-neon-purple text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                <IconComponent size={16} />
                {type.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-neon-purple mb-4"></div>
            <p className="text-gray-400">Loading codex items...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-12">
            <Package size={48} className="mx-auto mb-4 opacity-50 text-gray-500" />
            <p className="text-gray-400 mb-2">No codex items found</p>
            <p className="text-gray-500 text-sm mb-4">
              {searchTerm ? 'Try adjusting your search terms' : 'Create your first codex item to get started'}
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-neon-purple hover:bg-neon-purple/80 text-white px-4 py-2 rounded-lg flex items-center gap-2 mx-auto"
            >
              <Plus size={16} />
              Create First Item
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map(item => {
              const IconComponent = getTypeIcon(item.type)
              const typeColor = getTypeColor(item.type)
              
              return (
                <div key={item.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <IconComponent size={20} className={typeColor} />
                      <div>
                        <h3 className="font-semibold text-white">{item.name}</h3>
                        <span className="text-xs text-gray-400 capitalize">{item.type}</span>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => setEditingItem(item.id)}
                        className="p-1 text-gray-400 hover:text-neon-cyan transition-colors"
                        title="Edit item"
                      >
                        <Edit size={14} />
                      </button>
                      <button
                        className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                        title="Delete item"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                  
                  {item.description && (
                    <p className="text-gray-300 text-sm mb-3 line-clamp-3">
                      {item.description}
                    </p>
                  )}
                  
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.tags.slice(0, 3).map(tag => (
                        <span
                          key={tag}
                          className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {item.tags.length > 3 && (
                        <span className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded">
                          +{item.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Create Form Modal */}
      {showCreateForm && (
        <CodexCreateForm
          onClose={() => setShowCreateForm(false)}
          onItemCreated={(item) => {
            setShowCreateForm(false)
            loadItems()
            onItemCreated?.(item)
          }}
        />
      )}
    </div>
  )
}

interface CodexCreateFormProps {
  onClose: () => void
  onItemCreated: (item: CreateCodexItemResponse) => void
}

function CodexCreateForm({ onClose, onItemCreated }: CodexCreateFormProps) {
  const [itemType, setItemType] = useState('character')
  const [name, setName] = useState('')
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const characterFields = [
    { key: 'age', label: 'Age', type: 'number' },
    { key: 'occupation', label: 'Occupation', type: 'text' },
    { key: 'personality', label: 'Personality', type: 'textarea' },
    { key: 'background', label: 'Background', type: 'textarea' },
    { key: 'voice', label: 'Voice/Speech', type: 'textarea' },
    { key: 'arc', label: 'Character Arc', type: 'textarea' },
    { key: 'appearance', label: 'Appearance', type: 'textarea' }
  ]

  const locationFields = [
    { key: 'location_type', label: 'Location Type', type: 'text' },
    { key: 'description', label: 'Description', type: 'textarea' },
    { key: 'atmosphere', label: 'Atmosphere', type: 'textarea' },
    { key: 'significance', label: 'Significance', type: 'textarea' }
  ]

  const getFieldsForType = (type: string) => {
    switch (type) {
      case 'character':
        return characterFields
      case 'location':
        return locationFields
      default:
        return [
          { key: 'description', label: 'Description', type: 'textarea' },
          { key: 'notes', label: 'Notes', type: 'textarea' }
        ]
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    setLoading(true)
    setError(null)

    try {
      const request: CreateCodexItemRequest = {
        name: name.trim(),
        type: itemType,
        data: formData
      }

      const response = await api.post<CreateCodexItemResponse>('/codex/items', request)
      onItemCreated(response)
    } catch (err: any) {
      setError(err.message || 'Failed to create codex item')
    } finally {
      setLoading(false)
    }
  }

  const fields = getFieldsForType(itemType)

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">Create Codex Item</h2>
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

          {/* Name and Type */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Type *
              </label>
              <select
                value={itemType}
                onChange={(e) => setItemType(e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
              >
                <option value="character">Character</option>
                <option value="location">Location</option>
                <option value="organization">Organization</option>
                <option value="event">Event</option>
                <option value="object">Object</option>
              </select>
            </div>
          </div>

          {/* Dynamic Fields */}
          {fields.map(field => (
            <div key={field.key}>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {field.label}
              </label>
              {field.type === 'textarea' ? (
                <textarea
                  value={formData[field.key] || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, [field.key]: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple resize-none"
                  rows={3}
                />
              ) : (
                <input
                  type={field.type}
                  value={formData[field.key] || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    [field.key]: field.type === 'number' ? parseInt(e.target.value) || 0 : e.target.value 
                  }))}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-neon-purple focus:ring-1 focus:ring-neon-purple"
                />
              )}
            </div>
          ))}

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
              disabled={loading || !name.trim()}
              className="px-4 py-2 bg-neon-purple rounded-lg text-white hover:bg-neon-purple/80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Save size={16} />
              {loading ? 'Creating...' : 'Create Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}