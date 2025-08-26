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
      <nav className="flex space-x-0 overflow-x-auto scrollbar-hide" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              flex items-center justify-center gap-1 sm:gap-2 px-2 sm:px-4 lg:px-6 py-2 sm:py-3 
              text-xs sm:text-sm font-medium transition-all duration-300
              whitespace-nowrap border-b-2 hover:text-neon-cyan min-w-0 flex-1 sm:flex-none
              touch-manipulation
              ${activeTab === tab.id
                ? 'border-neon-purple text-neon-purple shadow-neon-purple/20'
                : 'border-transparent text-gray-400 hover:border-neon-cyan/50'
              }
            `}
          >
            <span className="text-base sm:text-lg">{tab.icon}</span>
            <span className="hidden sm:block">{tab.label}</span>
            <span className="block sm:hidden text-[10px] leading-tight">{tab.label.split(' ')[0]}</span>
            {tab.badge !== undefined && tab.badge > 0 && (
              <span className="bg-neon-purple text-[10px] sm:text-xs px-1 sm:px-2 py-0.5 sm:py-1 rounded-full min-w-[16px] h-4 sm:h-auto flex items-center justify-center">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  )
}