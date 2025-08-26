'use client'

import { ReactNode } from 'react'

interface Tab {
  id: string
  label: string
  icon: ReactNode
  badge?: number
}

interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onTabChange: (tabId: string) => void
}

export function Tabs({ tabs, activeTab, onTabChange }: TabsProps) {
  return (
    <div className="border-b border-dark-border">
      <nav className="flex space-x-1 overflow-x-auto" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              flex items-center gap-2 px-6 py-3 text-sm font-medium transition-all duration-300
              whitespace-nowrap border-b-2 hover:text-neon-cyan
              ${activeTab === tab.id
                ? 'border-neon-purple text-neon-purple shadow-neon-purple/20'
                : 'border-transparent text-gray-400 hover:border-neon-cyan/50'
              }
            `}
          >
            {tab.icon}
            {tab.label}
            {tab.badge !== undefined && tab.badge > 0 && (
              <span className="bg-neon-purple text-xs px-2 py-1 rounded-full">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  )
}