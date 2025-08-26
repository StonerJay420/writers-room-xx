'use client'

import React, { useState, useEffect } from 'react'
import { ChevronRight, ChevronDown, BookOpen, FileText, Plus, Edit3, MoreHorizontal } from 'lucide-react'
import { Scene, Act, Chapter, NavigationState } from '@/types'

interface ManuscriptNavigatorProps {
  scenes: Scene[]
  onSceneSelect: (scene: Scene) => void
  onCreateScene: (chapter: number, order: number) => void
  selectedSceneId?: string
}

export function ManuscriptNavigator({ 
  scenes, 
  onSceneSelect, 
  onCreateScene,
  selectedSceneId 
}: ManuscriptNavigatorProps) {
  const [navState, setNavState] = useState<NavigationState>({
    expandedActs: new Set([1]), // Start with Act 1 expanded
    expandedChapters: new Set([1]) // Start with Chapter 1 expanded
  })

  // Organize scenes into acts and chapters
  const organizeScenes = (): Act[] => {
    const actMap = new Map<number, Act>()
    
    // For now, we'll use a simple rule: every 5 chapters = 1 act
    // This can be made configurable later
    scenes.forEach(scene => {
      const actId = Math.ceil(scene.chapter / 5)
      const chapterId = scene.chapter
      
      if (!actMap.has(actId)) {
        actMap.set(actId, {
          id: actId,
          title: `Act ${actId}`,
          description: `Chapters ${(actId - 1) * 5 + 1} - ${actId * 5}`,
          chapters: []
        })
      }
      
      const act = actMap.get(actId)!
      let chapter = act.chapters.find(c => c.id === chapterId)
      
      if (!chapter) {
        chapter = {
          id: chapterId,
          act_id: actId,
          title: `Chapter ${chapterId}`,
          description: `Chapter ${chapterId}`,
          scenes: []
        }
        act.chapters.push(chapter)
      }
      
      chapter.scenes.push(scene)
    })
    
    // Sort acts, chapters, and scenes
    const acts = Array.from(actMap.values()).sort((a, b) => a.id - b.id)
    acts.forEach(act => {
      act.chapters.sort((a, b) => a.id - b.id)
      act.chapters.forEach(chapter => {
        chapter.scenes.sort((a, b) => a.order_in_chapter - b.order_in_chapter)
      })
    })
    
    return acts
  }

  const acts = organizeScenes()

  const toggleAct = (actId: number) => {
    const newExpanded = new Set(navState.expandedActs)
    if (newExpanded.has(actId)) {
      newExpanded.delete(actId)
    } else {
      newExpanded.add(actId)
    }
    setNavState(prev => ({ ...prev, expandedActs: newExpanded }))
  }

  const toggleChapter = (chapterId: number) => {
    const newExpanded = new Set(navState.expandedChapters)
    if (newExpanded.has(chapterId)) {
      newExpanded.delete(chapterId)
    } else {
      newExpanded.add(chapterId)
    }
    setNavState(prev => ({ ...prev, expandedChapters: newExpanded }))
  }

  const handleCreateScene = (chapterId: number) => {
    const chapter = acts.flatMap(a => a.chapters).find(c => c.id === chapterId)
    const nextOrder = chapter ? chapter.scenes.length + 1 : 1
    onCreateScene(chapterId, nextOrder)
  }

  return (
    <div className="h-full bg-gray-900 border-r border-gray-700 overflow-y-auto">
      <div className="p-3 sm:p-4 border-b border-gray-700">
        <h2 className="text-base sm:text-lg font-semibold text-white flex items-center gap-2">
          <BookOpen size={18} className="sm:w-5 sm:h-5" />
          <span className="hidden sm:block">Manuscript</span>
          <span className="block sm:hidden">MS</span>
        </h2>
      </div>
      
      <div className="p-1 sm:p-2">
        {acts.map(act => (
          <div key={act.id} className="mb-2">
            {/* Act Header */}
            <div 
              className="flex items-center gap-1 sm:gap-2 p-2 sm:p-3 rounded-lg hover:bg-gray-800 cursor-pointer group touch-manipulation"
              onClick={() => toggleAct(act.id)}
            >
              {navState.expandedActs.has(act.id) ? (
                <ChevronDown size={14} className="text-gray-400 sm:w-4 sm:h-4" />
              ) : (
                <ChevronRight size={14} className="text-gray-400 sm:w-4 sm:h-4" />
              )}
              <BookOpen size={14} className="text-neon-purple sm:w-4 sm:h-4" />
              <span className="text-white font-medium text-sm sm:text-base truncate">{act.title}</span>
              <span className="text-gray-400 text-xs sm:text-sm ml-auto hidden sm:block">{act.chapters.length} ch</span>
            </div>
            
            {/* Chapters */}
            {navState.expandedActs.has(act.id) && (
              <div className="ml-2 sm:ml-4 mt-1">
                {act.chapters.map(chapter => (
                  <div key={chapter.id} className="mb-1">
                    {/* Chapter Header */}
                    <div className="flex items-center gap-1 sm:gap-2 p-2 rounded-lg hover:bg-gray-800 cursor-pointer group touch-manipulation">
                      <div 
                        className="flex items-center gap-1 sm:gap-2 flex-1 min-w-0"
                        onClick={() => toggleChapter(chapter.id)}
                      >
                        {navState.expandedChapters.has(chapter.id) ? (
                          <ChevronDown size={12} className="text-gray-400 sm:w-[14px] sm:h-[14px] flex-shrink-0" />
                        ) : (
                          <ChevronRight size={12} className="text-gray-400 sm:w-[14px] sm:h-[14px] flex-shrink-0" />
                        )}
                        <FileText size={12} className="text-neon-cyan sm:w-[14px] sm:h-[14px] flex-shrink-0" />
                        <span className="text-gray-200 text-xs sm:text-sm truncate">{chapter.title}</span>
                        <span className="text-gray-500 text-[10px] sm:text-xs ml-auto flex-shrink-0">{chapter.scenes.length}</span>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleCreateScene(chapter.id)
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-700 transition-opacity touch-manipulation flex-shrink-0"
                        title="Add scene"
                      >
                        <Plus size={10} className="text-neon-green sm:w-3 sm:h-3" />
                      </button>
                    </div>
                    
                    {/* Scenes */}
                    {navState.expandedChapters.has(chapter.id) && (
                      <div className="ml-4 sm:ml-6 mt-1 space-y-1">
                        {chapter.scenes.map(scene => (
                          <div 
                            key={scene.id}
                            className={`flex items-center gap-1 sm:gap-2 p-2 rounded-lg cursor-pointer group transition-colors touch-manipulation ${
                              selectedSceneId === scene.id 
                                ? 'bg-neon-purple/20 border border-neon-purple/50' 
                                : 'hover:bg-gray-800'
                            }`}
                            onClick={() => onSceneSelect(scene)}
                          >
                            <Edit3 size={10} className="text-neon-pink sm:w-3 sm:h-3 flex-shrink-0" />
                            <span className="text-gray-300 text-xs sm:text-sm flex-1 truncate">
                              Scene {scene.order_in_chapter}
                            </span>
                            {scene.pov && (
                              <span className="text-neon-cyan text-[9px] sm:text-xs bg-gray-800 px-1 sm:px-2 py-0.5 sm:py-1 rounded flex-shrink-0">
                                {scene.pov}
                              </span>
                            )}
                            {scene.location && (
                              <span className="text-neon-green text-[9px] sm:text-xs bg-gray-800 px-1 sm:px-2 py-0.5 sm:py-1 rounded flex-shrink-0">
                                {scene.location}
                              </span>
                            )}
                          </div>
                        ))}
                        
                        {chapter.scenes.length === 0 && (
                          <div className="flex items-center gap-2 p-2 text-gray-500 text-sm">
                            <span>No scenes yet</span>
                            <button
                              onClick={() => handleCreateScene(chapter.id)}
                              className="text-neon-green hover:text-neon-green/80 flex items-center gap-1"
                            >
                              <Plus size={12} />
                              Add first scene
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {acts.length === 0 && (
          <div className="text-center p-8 text-gray-500">
            <BookOpen size={48} className="mx-auto mb-4 opacity-50" />
            <p className="mb-2">No scenes found</p>
            <p className="text-sm">Create your first scene to get started</p>
          </div>
        )}
      </div>
    </div>
  )
}