'use client'

import { useState } from 'react'
import { Upload, FolderOpen, RefreshCw, FileText, AlertTriangle, CheckCircle } from 'lucide-react'
import { FileUpload } from './FileUpload'

interface FileManagerProps {
  onUploadComplete: () => void
  onIndexFiles: () => void
}

export function FileManager({ onUploadComplete, onIndexFiles }: FileManagerProps) {
  const [showUpload, setShowUpload] = useState(false)
  const [indexing, setIndexing] = useState(false)
  const [lastIndexed, setLastIndexed] = useState<Date | null>(null)

  const handleIndexFiles = async () => {
    setIndexing(true)
    try {
      await onIndexFiles()
      setLastIndexed(new Date())
    } finally {
      setIndexing(false)
    }
  }

  const handleUploadComplete = () => {
    onUploadComplete()
    setShowUpload(false)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-display font-bold gradient-text mb-2">
          File Management
        </h2>
        <p className="text-gray-400">
          Upload manuscript files and manage your content library
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="neon-card rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-neon-purple/10">
              <Upload className="w-6 h-6 text-neon-purple" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-neon-purple mb-2">
                Upload Files
              </h3>
              <p className="text-gray-400 text-sm mb-4">
                Upload manuscript and codex files to your library. Supports Markdown (.md) files.
              </p>
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="neon-button rounded-lg px-4 py-2"
              >
                {showUpload ? 'Cancel' : 'Select Files'}
              </button>
            </div>
          </div>
        </div>

        <div className="neon-card rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-neon-cyan/10">
              <RefreshCw className={`w-6 h-6 text-neon-cyan ${indexing ? 'animate-spin' : ''}`} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-neon-cyan mb-2">
                Index Content
              </h3>
              <p className="text-gray-400 text-sm mb-4">
                Process uploaded files and extract scenes for AI analysis.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleIndexFiles}
                  disabled={indexing}
                  className="neon-button rounded-lg px-4 py-2 disabled:opacity-50"
                >
                  {indexing ? 'Indexing...' : 'Start Indexing'}
                </button>
                {lastIndexed && (
                  <span className="text-xs text-gray-500">
                    Last: {lastIndexed.toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Interface */}
      {showUpload && (
        <div className="neon-card rounded-lg p-6">
          <h3 className="text-lg font-display font-semibold mb-4 neon-text">
            Upload Manuscript Files
          </h3>
          <FileUpload onUploadComplete={handleUploadComplete} />
        </div>
      )}

      {/* File Structure Guide */}
      <div className="neon-card rounded-lg p-6">
        <h3 className="text-lg font-display font-semibold mb-4 flex items-center gap-2">
          <FolderOpen className="w-5 h-5 text-neon-green" />
          File Structure Guide
        </h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-neon-purple mb-3">Manuscript Files</h4>
            <div className="bg-dark-surface/50 rounded-lg p-4 font-mono text-sm">
              <div className="text-gray-400">data/manuscript/</div>
              <div className="ml-4 text-neon-cyan">├── chapter-01/</div>
              <div className="ml-8 text-gray-300">├── scene-001.md</div>
              <div className="ml-8 text-gray-300">├── scene-002.md</div>
              <div className="ml-8 text-gray-300">└── scene-003.md</div>
              <div className="ml-4 text-neon-cyan">├── chapter-02/</div>
              <div className="ml-8 text-gray-300">└── ...</div>
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold text-neon-pink mb-3">Codex Files</h4>
            <div className="bg-dark-surface/50 rounded-lg p-4 font-mono text-sm">
              <div className="text-gray-400">data/codex/</div>
              <div className="ml-4 text-neon-cyan">├── characters/</div>
              <div className="ml-8 text-gray-300">├── protagonist.md</div>
              <div className="ml-8 text-gray-300">└── antagonist.md</div>
              <div className="ml-4 text-neon-cyan">├── world/</div>
              <div className="ml-8 text-gray-300">├── locations.md</div>
              <div className="ml-8 text-gray-300">└── history.md</div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-start gap-3 p-3 bg-neon-green/10 rounded-lg border border-neon-green/20">
            <CheckCircle className="w-5 h-5 text-neon-green mt-0.5" />
            <div>
              <p className="font-semibold text-neon-green text-sm">Supported</p>
              <p className="text-gray-400 text-xs">Markdown (.md) files</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-3 bg-neon-yellow/10 rounded-lg border border-neon-yellow/20">
            <AlertTriangle className="w-5 h-5 text-neon-yellow mt-0.5" />
            <div>
              <p className="font-semibold text-neon-yellow text-sm">Required</p>
              <p className="text-gray-400 text-xs">Proper scene headers</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-3 bg-neon-purple/10 rounded-lg border border-neon-purple/20">
            <FileText className="w-5 h-5 text-neon-purple mt-0.5" />
            <div>
              <p className="font-semibold text-neon-purple text-sm">Max Size</p>
              <p className="text-gray-400 text-xs">10MB per file</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}