'use client'

import { useState } from 'react'
import { TextEditor } from '@/components/TextEditor'
import { FileUpload } from '@/components/FileUpload'

export default function EditorPage() {
  const [currentFile, setCurrentFile] = useState<{
    name: string
    content: string
  } | null>(null)

  const handleFileUploaded = async () => {
    // Refresh or load the uploaded file content
    // For now, we'll let the user manually enter text
    console.log('File uploaded successfully')
  }

  const handleSaveText = async (text: string) => {
    if (!currentFile) {
      console.log('Saving new text:', text)
      // In a real app, you might want to prompt for a filename
      return
    }

    try {
      // Save the updated text back to the server
      console.log('Saving changes to:', currentFile.name, text)
      // You could implement a save endpoint here
    } catch (error) {
      console.error('Failed to save text:', error)
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Manuscript Editor
        </h1>
        <p className="text-gray-600 mt-2">
          Upload your manuscript files and get AI-powered editing suggestions
        </p>
      </div>

      {/* File Upload Section */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Upload Files</h2>
        <FileUpload onUploadComplete={handleFileUploaded} />
      </div>

      {/* Text Editor Section */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Editor</h2>
        <TextEditor
          initialText={currentFile?.content || 'Start typing your manuscript here, or paste existing text to get AI-powered editing suggestions...'}
          onSave={handleSaveText}
          fileName={currentFile?.name}
        />
      </div>
    </div>
  )
}