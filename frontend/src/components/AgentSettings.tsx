'use client'

import { useState } from 'react'
import { Brain, Settings, Save, RotateCcw, AlertCircle, CheckCircle } from 'lucide-react'
import { ModelSelector } from './ModelSelector'

interface ModelPreferences {
  lore_archivist: string
  grim_editor: string
  tone_metrics: string
  supervisor: string
}

interface AgentSettingsProps {
  modelPreferences: ModelPreferences
  onModelChange: (agentName: string, modelId: string) => void
}

export function AgentSettings({ modelPreferences, onModelChange }: AgentSettingsProps) {
  const [hasChanges, setHasChanges] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  const agents = [
    {
      id: 'lore_archivist',
      name: 'Lore Archivist',
      description: 'Canon consistency checker and lore expert. Validates character consistency, world-building, and canon adherence across scenes.',
      icon: '📚',
      color: 'neon-cyan',
      capabilities: ['Character consistency', 'World-building validation', 'Canon checking', 'Reference linking']
    },
    {
      id: 'grim_editor',
      name: 'Grim Editor',
      description: 'Line editor focused on prose improvement. Enhances grammar, style, flow, and word choice for better readability.',
      icon: '✏️',
      color: 'neon-green',
      capabilities: ['Grammar correction', 'Style improvement', 'Flow enhancement', 'Word choice optimization']
    },
    {
      id: 'tone_metrics',
      name: 'Tone Metrics',
      description: 'Writing quality and tone analyzer. Measures readability, analyzes tone consistency, and evaluates pacing.',
      icon: '📊',
      color: 'neon-pink',
      capabilities: ['Readability analysis', 'Tone consistency', 'Pacing evaluation', 'Voice analysis']
    },
    {
      id: 'supervisor',
      name: 'Supervisor',
      description: 'Senior editor providing strategic guidance. Focuses on story structure, character development, and thematic coherence.',
      icon: '🎯',
      color: 'neon-purple',
      capabilities: ['Story structure', 'Character development', 'Thematic coherence', 'Strategic guidance']
    }
  ]

  const handleModelChange = (agentName: string, modelId: string) => {
    onModelChange(agentName, modelId)
    setHasChanges(true)
    setSaveStatus('idle')
  }

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      // The model changes are already saved individually through handleModelChange
      // This button now just resets the visual state
      setSaveStatus('saved')
      setHasChanges(false)
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch (error) {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    }
  }

  const handleReset = () => {
    // Reset to defaults
    const defaults = {
      lore_archivist: 'anthropic/claude-sonnet-4-20250514',
      grim_editor: 'openai/gpt-5',
      tone_metrics: 'anthropic/claude-sonnet-4-20250514',
      supervisor: 'anthropic/claude-sonnet-4-20250514'
    }
    
    Object.entries(defaults).forEach(([agent, model]) => {
      onModelChange(agent, model)
    })
    setHasChanges(false)
    setSaveStatus('idle')
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-display font-bold gradient-text">
            Agent Configuration
          </h2>
          <p className="text-gray-400 mt-1">
            Configure AI models for each specialized editing agent
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {hasChanges && (
            <div className="flex items-center gap-2 text-neon-yellow text-sm">
              <AlertCircle size={16} />
              Unsaved changes
            </div>
          )}
          
          <button
            onClick={handleReset}
            className="neon-button rounded-lg px-4 py-2 flex items-center gap-2"
          >
            <RotateCcw size={16} />
            Reset to Defaults
          </button>
          
          <button
            onClick={handleSave}
            disabled={!hasChanges || saveStatus === 'saving'}
            className={`
              px-4 py-2 rounded-lg flex items-center gap-2 transition-all duration-300
              ${hasChanges && saveStatus !== 'saving'
                ? 'bg-gradient-to-r from-neon-green to-neon-cyan hover:shadow-neon-green hover:scale-105'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            {saveStatus === 'saving' ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Saving...
              </>
            ) : saveStatus === 'saved' ? (
              <>
                <CheckCircle size={16} />
                Saved
              </>
            ) : (
              <>
                <Save size={16} />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {agents.map((agent) => (
          <div key={agent.id} className="neon-card rounded-lg p-6 space-y-4">
            <div className="flex items-start gap-4">
              <div className="text-2xl p-3 rounded-lg bg-neon-purple/10">
                {agent.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-display font-semibold text-neon-purple mb-2">
                  {agent.name}
                </h3>
                <p className="text-gray-400 text-sm mb-3">
                  {agent.description}
                </p>
                
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Capabilities
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {agent.capabilities.map((capability) => (
                      <span
                        key={capability}
                        className="px-2 py-1 text-xs rounded bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30"
                      >
                        {capability}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="border-t border-dark-border pt-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                AI Model
              </label>
              <ModelSelector
                agentName={agent.id}
                currentModel={modelPreferences[agent.id as keyof ModelPreferences]}
                onModelChange={handleModelChange}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Performance Settings */}
      <div className="neon-card rounded-lg p-6">
        <h3 className="text-lg font-display font-semibold mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5 text-neon-purple" />
          Performance Settings
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Processing Mode
            </label>
            <select className="w-full neon-input rounded-md px-3 py-2">
              <option value="sequential">Sequential (Safe)</option>
              <option value="parallel">Parallel (Fast)</option>
              <option value="adaptive">Adaptive (Smart)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Quality Level
            </label>
            <select className="w-full neon-input rounded-md px-3 py-2">
              <option value="draft">Draft (Fast)</option>
              <option value="standard">Standard (Balanced)</option>
              <option value="premium">Premium (Thorough)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Timeout (seconds)
            </label>
            <input
              type="number"
              min="30"
              max="300"
              defaultValue="120"
              className="w-full neon-input rounded-md px-3 py-2"
            />
          </div>
        </div>
      </div>
    </div>
  )
}