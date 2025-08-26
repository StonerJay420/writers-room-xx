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
