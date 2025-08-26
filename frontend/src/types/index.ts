export interface Scene {
  id: string
  chapter: number
  order_in_chapter: number
  pov?: string
  location?: string
  word_count?: number
  created_at?: string
  updated_at?: string
  last_processed?: string
  beats_json?: any
  links_json?: any
}

export interface ModelPreferences {
  lore_archivist: string
  grim_editor: string
  tone_metrics: string
  supervisor: string
}

export interface SceneDetail {
  meta: {
    id: string
    chapter: number
    order_in_chapter: number
    pov: string
    location: string
    text_path: string
    beats_json: string[]
    links_json: string[]
    created_at: string
    updated_at: string
  }
  content: string
}

export interface Metrics {
  flesch_reading_ease?: number
  flesch_kincaid_grade?: number
  sentence_count?: number
  word_count?: number
  avg_sentence_length?: number
  syllable_count?: number
  avg_syllables_per_word?: number
  dialogue_proportion?: number
  active_voice_ratio?: number
  target_analysis?: {
    [key: string]: {
      value: number
      target: number
      status: 'good' | 'okay' | 'needs_improvement'
      deviation: number
    }
  }
}

export interface CanonReceipt {
  type: string
  element: string
  source: string
  context: string
}

export interface Patch {
  id: string
  scene_id: string
  variant: string
  diff: string
  metrics_before: Metrics
  metrics_after: Metrics
  canon_receipts: CanonReceipt[]
  rationale: string
  changes_summary: {
    total_changes: number
    additions: number
    deletions: number
    added_lines: string[]
    deleted_lines: string[]
  }
  created_at: string
}

export interface PassResult {
  scene_id: string
  variants: {
    [key: string]: {
      patch_id: string
      diff: string
      metrics_after: Metrics
      summary: any
    }
  }
  reports: {
    metrics: {
      before: Metrics
    }
    canon_receipts: CanonReceipt[]
    rationales: {
      [key: string]: string
    }
  }
}

export interface Job {
  id: string
  scene_id: string
  status: 'queued' | 'running' | 'done' | 'error'
  agents_json: string[]
  result_json: PassResult | null
  created_at: string
  updated_at: string
}

// Codex item types
export interface CodexItem {
  id: string
  name: string
  type: string
  description?: string
  tags?: string[]
  metadata?: Record<string, any>
  created_at?: string
  updated_at?: string
}

export interface Character {
  id: string
  name: string
  age?: number
  occupation?: string
  personality?: string
  background?: string
  voice?: string
  arc?: string
  appearance?: string
  relationships?: Record<string, string>
  tags?: string[]
  notes?: string
}

export interface Location {
  id: string
  name: string
  type?: string
  description?: string
  atmosphere?: string
  significance?: string
  connected_locations?: string[]
  tags?: string[]
  notes?: string
}

export interface CreateCodexItemRequest {
  name: string
  type: string
  data: Record<string, any>
}

export interface CreateCodexItemResponse {
  id: string
  name: string
  type: string
  path: string
  status: string
}

// Scene creation types
export interface CreateSceneRequest {
  chapter: number
  order_in_chapter: number
  title?: string
  pov?: string
  location?: string
  beats?: string[]
  content: string
  links?: Record<string, any>
}

export interface CreateSceneResponse {
  id: string
  chapter: number
  order_in_chapter: number
  path: string
  status: string
}

// Navigation and hierarchy types
export interface Act {
  id: number
  title: string
  description?: string
  chapters: Chapter[]
}

export interface Chapter {
  id: number
  act_id: number
  title: string
  description?: string
  scenes: Scene[]
}

export interface SceneNode extends Scene {
  title?: string
  description?: string
}

export interface NavigationState {
  selectedAct?: number
  selectedChapter?: number
  selectedScene?: string
  expandedActs: Set<number>
  expandedChapters: Set<number>
}
