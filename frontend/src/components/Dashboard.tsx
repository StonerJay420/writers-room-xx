'use client'

import { FileText, Zap, Clock, TrendingUp, BookOpen } from 'lucide-react'
import { Scene } from '@/types'

interface DashboardProps {
  scenes: Scene[]
  onProcessScene: (sceneId: string) => void
  processingScene: string | null
}

export function Dashboard({ scenes, onProcessScene, processingScene }: DashboardProps) {
  const totalScenes = scenes.length
  const chapters = [...new Set(scenes.map(s => s.chapter))].length
  const recentlyProcessed = scenes.filter(s => s.last_processed).length

  const stats = [
    {
      label: 'Total Scenes',
      value: totalScenes,
      icon: FileText,
      color: 'neon-cyan'
    },
    {
      label: 'Chapters',
      value: chapters,
      icon: BookOpen,
      color: 'neon-purple'
    },
    {
      label: 'Processed',
      value: recentlyProcessed,
      icon: Zap,
      color: 'neon-green'
    },
    {
      label: 'Queue',
      value: totalScenes - recentlyProcessed,
      icon: Clock,
      color: 'neon-pink'
    }
  ]

  const recentScenes = scenes
    .sort((a, b) => (b.last_processed || '').localeCompare(a.last_processed || ''))
    .slice(0, 5)

  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const IconComponent = stat.icon
          return (
            <div key={stat.label} className="neon-card rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">{stat.label}</p>
                  <p className={`text-3xl font-bold text-${stat.color}`}>
                    {stat.value}
                  </p>
                </div>
                <div className={`p-3 rounded-lg bg-${stat.color}/10`}>
                  <IconComponent className={`w-6 h-6 text-${stat.color}`} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="neon-card rounded-lg p-6">
        <h2 className="text-xl font-display font-semibold mb-4 neon-text">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="neon-button rounded-lg p-4 text-left hover:scale-105">
            <div className="flex items-center gap-3">
              <Zap className="w-5 h-5 text-neon-purple" />
              <div>
                <h3 className="font-semibold">Process All Scenes</h3>
                <p className="text-sm text-gray-400">Run AI agents on all scenes</p>
              </div>
            </div>
          </button>
          
          <button className="neon-button rounded-lg p-4 text-left hover:scale-105">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-5 h-5 text-neon-cyan" />
              <div>
                <h3 className="font-semibold">Generate Report</h3>
                <p className="text-sm text-gray-400">Create analysis summary</p>
              </div>
            </div>
          </button>
          
          <button className="neon-button rounded-lg p-4 text-left hover:scale-105">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-neon-green" />
              <div>
                <h3 className="font-semibold">Export Changes</h3>
                <p className="text-sm text-gray-400">Download edited manuscript</p>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="neon-card rounded-lg p-6">
        <h2 className="text-xl font-display font-semibold mb-4 neon-text">
          Recent Activity
        </h2>
        {recentScenes.length === 0 ? (
          <p className="text-gray-400 py-4">No recent activity. Start processing scenes to see updates here.</p>
        ) : (
          <div className="space-y-3">
            {recentScenes.map((scene) => (
              <div key={scene.id} className="flex items-center justify-between p-3 bg-dark-surface/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse"></div>
                  <div>
                    <h4 className="font-medium">{scene.id}</h4>
                    <p className="text-sm text-gray-400">Chapter {scene.chapter}</p>
                  </div>
                </div>
                <button
                  onClick={() => onProcessScene(scene.id)}
                  disabled={processingScene === scene.id}
                  className="text-sm neon-button px-4 py-2 rounded"
                >
                  {processingScene === scene.id ? 'Processing...' : 'Reprocess'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}