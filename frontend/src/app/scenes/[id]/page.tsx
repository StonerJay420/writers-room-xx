'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { SceneDetail, Patch, PassResult } from '@/types'
import { api } from '@/lib/api'
import { DiffViewer } from '@/components/DiffViewer'
import { MetricsPanel } from '@/components/MetricsPanel'
import { ArrowLeft, Play, Save, AlertTriangle } from 'lucide-react'
import Link from 'next/link'

export default function ScenePage() {
  const params = useParams()
  const sceneId = params.id as string
  
  const [scene, setScene] = useState<SceneDetail | null>(null)
  const [patches, setPatches] = useState<Patch[]>([])
  const [selectedVariant, setSelectedVariant] = useState<string>('safe')
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [passResult, setPassResult] = useState<PassResult | null>(null)

  useEffect(() => {
    if (sceneId) {
      loadScene()
      loadPatches()
    }
  }, [sceneId])

  const loadScene = async () => {
    try {
      const response = await api.get<{ id: string; text: string; path: string }>(`/scenes/${sceneId}`)
      
      // Transform API response to match SceneDetail interface
      const sceneData: SceneDetail = {
        meta: {
          id: response.id,
          chapter: parseInt(response.id.match(/ch(\d+)/)?.[1] || '1'),
          order_in_chapter: parseInt(response.id.match(/s(\d+)/)?.[1] || '1'),
          pov: 'Unknown', // These would need to come from scene metadata
          location: 'Unknown',
          text_path: response.path,
          beats_json: [],
          links_json: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        content: response.text
      }
      
      setScene(sceneData)
    } catch (error) {
      console.error('Failed to load scene:', error)
    }
  }

  const loadPatches = async () => {
    try {
      const patchesData = await api.get<Patch[]>(`/patches/${sceneId}`)
      setPatches(patchesData)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load patches:', error)
      setLoading(false)
    }
  }

  const runPass = async () => {
    try {
      setProcessing(true)
      const result = await api.post<{ result: PassResult }>('/passes/run', {
        scene_id: sceneId,
        agents: ['lore_archivist', 'grim_editor'],
        edge_intensity: 1
      })
      
      setPassResult(result.result)
      await loadPatches() // Reload patches after processing
    } catch (error) {
      console.error('Pass failed:', error)
      alert('Failed to run editing pass')
    } finally {
      setProcessing(false)
    }
  }

  const applyPatch = async () => {
    try {
      await api.post<void>('/patches/apply', {
        scene_id: sceneId,
        variant: selectedVariant,
        commit_message: `Apply ${selectedVariant} patch for ${sceneId}`
      })
      
      alert(`Applied ${selectedVariant} patch successfully!`)
      await loadScene() // Reload scene content
    } catch (error) {
      console.error('Failed to apply patch:', error)
      alert('Failed to apply patch')
    }
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="mt-2 text-gray-600">Loading scene...</p>
      </div>
    )
  }

  if (!scene) {
    return (
      <div className="text-center py-8">
        <AlertTriangle size={48} className="mx-auto text-red-400 mb-4" />
        <p className="text-gray-600">Scene not found</p>
        <Link href="/" className="btn btn-primary mt-4">
          Back to Scenes
        </Link>
      </div>
    )
  }

  const currentPatch = patches.find(p => p.variant === selectedVariant)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/" className="btn btn-secondary flex items-center space-x-2">
            <ArrowLeft size={16} />
            <span>Back</span>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{scene.meta.id}</h1>
            <p className="text-gray-600">
              Chapter {scene.meta.chapter} • {scene.meta.pov} • {scene.meta.location}
            </p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={runPass}
            disabled={processing}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Play size={16} />
            <span>{processing ? 'Processing...' : 'Run AI Pass'}</span>
          </button>
          {currentPatch && (
            <button
              onClick={applyPatch}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <Save size={16} />
              <span>Apply {selectedVariant}</span>
            </button>
          )}
        </div>
      </div>

      {/* Variant Selector */}
      {patches.length > 0 && (
        <div className="card p-4">
          <div className="flex space-x-2">
            {patches.map(patch => (
              <button
                key={patch.variant}
                onClick={() => setSelectedVariant(patch.variant)}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  selectedVariant === patch.variant
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {patch.variant.charAt(0).toUpperCase() + patch.variant.slice(1)}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Diff Viewer */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4">
              {currentPatch ? `${selectedVariant} Variant` : 'Original Scene'}
            </h2>
            <DiffViewer
              originalText={scene.content}
              modifiedText={currentPatch?.diff || scene.content}
              isDiff={!!currentPatch}
            />
          </div>

          {/* Rationale */}
          {currentPatch?.rationale && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-3">AI Rationale</h3>
              <p className="text-gray-700">{currentPatch.rationale}</p>
            </div>
          )}
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          {/* Metrics */}
          {currentPatch && (
            <MetricsPanel
              beforeMetrics={currentPatch.metrics_before}
              afterMetrics={currentPatch.metrics_after}
            />
          )}

          {/* Canon Receipts */}
          {currentPatch?.canon_receipts && currentPatch.canon_receipts.length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-3">Canon References</h3>
              <div className="space-y-3">
                {currentPatch.canon_receipts.map((receipt, index) => (
                  <div key={index} className="p-3 bg-blue-50 rounded-md">
                    <div className="font-medium text-blue-900">
                      {receipt.element}
                    </div>
                    <div className="text-sm text-blue-700 mt-1">
                      {receipt.source}
                    </div>
                    <div className="text-xs text-blue-600 mt-1">
                      {receipt.context}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Patch Summary */}
          {currentPatch && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-3">Changes Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Total Changes:</span>
                  <span className="font-medium">{currentPatch.changes_summary?.total_changes || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Additions:</span>
                  <span className="font-medium text-green-600">+{currentPatch.changes_summary?.additions || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Deletions:</span>
                  <span className="font-medium text-red-600">-{currentPatch.changes_summary?.deletions || 0}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
