'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { Upload, File, Check, AlertCircle } from 'lucide-react'

interface FileUploadProps {
  onUploadComplete?: () => void
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [uploadResults, setUploadResults] = useState<Array<{
    filename: string
    status: 'success' | 'error'
    message: string
  }>>([])

  const handleFiles = async (files: FileList) => {
    setUploading(true)
    setUploadResults([])
    
    const results = []
    
    for (const file of Array.from(files)) {
      if (!file.name.endsWith('.md')) {
        results.push({
          filename: file.name,
          status: 'error' as const,
          message: 'Only .md files are supported'
        })
        continue
      }

      try {
        const formData = new FormData()
        formData.append('file', file)
        
        // Determine file type based on filename or let user choose
        const fileType = file.name.includes('codex') ? 'codex' : 'manuscript'
        formData.append('file_type', fileType)

        await api.post('/ingest/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        results.push({
          filename: file.name,
          status: 'success' as const,
          message: `Uploaded as ${fileType} file`
        })
      } catch (error) {
        results.push({
          filename: file.name,
          status: 'error' as const,
          message: error instanceof Error ? error.message : 'Upload failed'
        })
      }
    }
    
    setUploadResults(results)
    setUploading(false)
    
    if (onUploadComplete && results.some(r => r.status === 'success')) {
      onUploadComplete()
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files)
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <Upload size={48} className={`mx-auto mb-4 ${dragActive ? 'text-primary-500' : 'text-gray-400'}`} />
        <p className="text-lg font-medium text-gray-700 mb-2">
          Drop markdown files here
        </p>
        <p className="text-gray-500 mb-4">
          or click to browse
        </p>
        <input
          type="file"
          multiple
          accept=".md"
          onChange={handleFileInput}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="btn btn-primary cursor-pointer"
        >
          Choose Files
        </label>
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-600">Uploading files...</p>
        </div>
      )}

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700">Upload Results</h4>
          {uploadResults.map((result, index) => (
            <div 
              key={index}
              className={`flex items-center space-x-3 p-3 rounded-md ${
                result.status === 'success' 
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              {result.status === 'success' ? (
                <Check size={16} className="text-green-600" />
              ) : (
                <AlertCircle size={16} className="text-red-600" />
              )}
              <File size={16} />
              <div className="flex-1">
                <div className="font-medium">{result.filename}</div>
                <div className="text-sm opacity-75">{result.message}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
