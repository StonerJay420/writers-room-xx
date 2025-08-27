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
      <body className="bg-dark-bg min-h-screen">
        <ThemeProvider>
          <header className="bg-dark-surface/90 backdrop-blur-md border-b border-neon-purple/20 shadow-lg relative z-10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-4">
                <div className="flex items-center space-x-4">
                  <h1 className="text-2xl font-bold gradient-text animate-glow">
                    Writers Room X
                  </h1>
                  <nav className="flex space-x-4">
                    <a href="/" className="text-neon-cyan/80 hover:text-neon-cyan transition-colors duration-300 hover:drop-shadow-[0_0_8px_rgba(0,255,255,0.5)]">
                      Scenes
                    </a>
                    <a href="/upload" className="text-neon-cyan/80 hover:text-neon-cyan transition-colors duration-300 hover:drop-shadow-[0_0_8px_rgba(0,255,255,0.5)]">
                      Upload
                    </a>
                    <a href="/editor" className="text-neon-cyan/80 hover:text-neon-cyan transition-colors duration-300 hover:drop-shadow-[0_0_8px_rgba(0,255,255,0.5)]">
                      Editor
                    </a>
                  </nav>
                </div>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  )
}
