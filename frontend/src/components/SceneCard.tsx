'use client'

import { useState } from 'react'
import { ChevronRight, Zap, MapPin, User, Hash } from 'lucide-react'

interface SceneCardProps {
  scene: {
    id: string
    chapter: number
    order_in_chapter: number
    pov?: string
    location?: string
    beats_json?: any
  }
  onProcess: (sceneId: string) => void
  isProcessing: boolean
  compact?: boolean
}

export function SceneCard({ scene, onProcess, isProcessing, compact = false }: SceneCardProps) {
  const [expanded, setExpanded] = useState(false)
  const beats = scene.beats_json ? JSON.parse(scene.beats_json) : []

  return (
    <div className={`neon-card rounded-lg hover:shadow-neon-purple/20 transition-all duration-300 ${
      compact ? 'p-4 space-y-2' : 'p-6 space-y-4'
    }`}>
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <h3 className="text-lg font-display font-semibold gradient-text">
            Scene {scene.id}
          </h3>
          <div className="flex flex-wrap gap-3 text-sm">
            <span className="flex items-center gap-1 text-neon-cyan/70">
              <Hash size={14} />
              Chapter {scene.chapter}
            </span>
            {scene.pov && (
              <span className="flex items-center gap-1 text-neon-green/70">
                <User size={14} />
                {scene.pov}
              </span>
            )}
            {scene.location && (
              <span className="flex items-center gap-1 text-neon-pink/70">
                <MapPin size={14} />
                {scene.location}
              </span>
            )}
          </div>
        </div>
        
        <button
          onClick={() => onProcess(scene.id)}
          disabled={isProcessing}
          className={`
            px-4 py-2 rounded-lg flex items-center gap-2 transition-all duration-300
            ${isProcessing 
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
              : 'bg-gradient-to-r from-neon-purple to-neon-cyan hover:shadow-neon-cyan hover:scale-105'
            }
          `}
        >
          <Zap size={16} />
          {isProcessing ? 'Processing...' : 'Process'}
        </button>
      </div>

      {beats.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-sm text-neon-cyan/60 hover:text-neon-cyan transition-colors"
          >
            <ChevronRight 
              size={16} 
              className={`transform transition-transform ${expanded ? 'rotate-90' : ''}`}
            />
            {beats.length} Story Beats
          </button>
          
          {expanded && (
            <div className="pl-6 space-y-1">
              {beats.map((beat: string, idx: number) => (
                <div 
                  key={idx}
                  className="text-sm text-gray-400 pl-3 border-l-2 border-neon-purple/20 hover:border-neon-purple/50 transition-colors"
                >
                  {beat}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}