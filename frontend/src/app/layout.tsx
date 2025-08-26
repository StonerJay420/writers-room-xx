import type { Metadata } from 'next'
import './globals.css'
import { ThemeProvider } from '@/contexts/ThemeContext'

export const metadata: Metadata = {
  title: 'Writers Room X',
  description: 'AI-powered manuscript editing system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <ThemeProvider>
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-4">
                <div className="flex items-center space-x-4">
                  <h1 className="text-2xl font-bold text-gray-900">
                    Writers Room X
                  </h1>
                  <nav className="flex space-x-4">
                    <a href="/" className="text-gray-600 hover:text-gray-900">
                      Scenes
                    </a>
                    <a href="/upload" className="text-gray-600 hover:text-gray-900">
                      Upload
                    </a>
                    <a href="/editor" className="text-gray-600 hover:text-gray-900">
                      Editor
                    </a>
                  </nav>
                </div>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  )
}
