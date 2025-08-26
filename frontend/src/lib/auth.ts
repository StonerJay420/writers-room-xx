// Authentication and session management for OpenRouter BYOK
export class AuthManager {
  private static API_KEY_STORAGE = 'wrx_api_key'
  private static OPENROUTER_KEY_STORAGE = 'wrx_openrouter_key'
  
  static async getOrCreateSession(): Promise<string> {
    // Check if we already have a valid API key
    let apiKey = localStorage.getItem(this.API_KEY_STORAGE)
    
    if (apiKey) {
      // Verify the key is still valid
      try {
        const response = await fetch('/api/auth/status', {
          headers: {
            'Authorization': `Bearer ${apiKey}`
          }
        })
        
        if (response.ok) {
          return apiKey!
        }
      } catch (error) {
        console.log('Existing API key invalid, creating new session')
      }
    }
    
    // Create a new session
    try {
      const response = await fetch('/api/auth/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: `User_${new Date().getTime()}`
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        const newApiKey = data.api_key as string
        localStorage.setItem(this.API_KEY_STORAGE, newApiKey)
        return newApiKey
      } else {
        throw new Error('Failed to create session')
      }
    } catch (error) {
      console.error('Failed to create session:', error)
      throw error
    }
  }
  
  static getApiKey(): string | null {
    return localStorage.getItem(this.API_KEY_STORAGE)
  }
  
  static async hasOpenRouterKey(): Promise<boolean> {
    try {
      // Ensure we have a session first
      const apiKey = await this.getOrCreateSession()
      
      const response = await fetch('/api/auth/llm-key', {
        headers: {
          'Authorization': `Bearer ${apiKey}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        return data.has_key
      }
    } catch (error) {
      console.error('Failed to check OpenRouter key status:', error)
    }
    
    return false
  }
  
  static async setOpenRouterKey(openrouterKey: string): Promise<boolean> {
    const apiKey = await this.getOrCreateSession()
    
    try {
      const response = await fetch('/api/auth/llm-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          openrouter_api_key: openrouterKey
        })
      })
      
      if (response.ok) {
        localStorage.setItem(this.OPENROUTER_KEY_STORAGE, 'configured')
        return true
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to store OpenRouter key')
      }
    } catch (error) {
      console.error('Failed to store OpenRouter key:', error)
      throw error
    }
  }
  
  static async removeOpenRouterKey(): Promise<void> {
    const apiKey = this.getApiKey()
    if (!apiKey) return
    
    try {
      await fetch('/api/auth/llm-key', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${apiKey}`
        }
      })
      localStorage.removeItem(this.OPENROUTER_KEY_STORAGE)
    } catch (error) {
      console.error('Failed to remove OpenRouter key:', error)
    }
  }
  
  static clearSession(): void {
    localStorage.removeItem(this.API_KEY_STORAGE)
    localStorage.removeItem(this.OPENROUTER_KEY_STORAGE)
  }
}