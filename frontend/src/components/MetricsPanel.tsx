'use client'

interface Metrics {
  target_analysis?: {
    [key: string]: {
      value: number
      target: number
      status: 'good' | 'okay' | 'needs_improvement'
      deviation: number
    }
  }
  flesch_reading_ease?: number
  avg_sentence_length?: number
  word_count?: number
  sentence_count?: number
}

interface MetricsPanelProps {
  beforeMetrics: Metrics
  afterMetrics: Metrics
}

export function MetricsPanel({ beforeMetrics, afterMetrics }: MetricsPanelProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-600 bg-green-100'
      case 'okay': return 'text-yellow-600 bg-yellow-100'
      case 'needs_improvement': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const formatValue = (value: number) => {
    return typeof value === 'number' ? value.toFixed(2) : 'N/A'
  }

  const renderMetricRow = (key: string, before: any, after: any) => {
    const beforeVal = before?.value ?? before
    const afterVal = after?.value ?? after
    const status = after?.status ?? 'unknown'
    const target = after?.target

    return (
      <div key={key} className="grid grid-cols-4 gap-2 py-2 text-sm">
        <div className="font-medium text-gray-700 capitalize">
          {key.replace(/_/g, ' ')}
        </div>
        <div className="text-center">{formatValue(beforeVal)}</div>
        <div className="text-center">{formatValue(afterVal)}</div>
        <div className="text-center">
          <span className={`px-2 py-1 rounded text-xs ${getStatusColor(status)}`}>
            {status}
          </span>
        </div>
      </div>
    )
  }

  // Get all unique metric keys
  const beforeAnalysis = beforeMetrics?.target_analysis || {}
  const afterAnalysis = afterMetrics?.target_analysis || {}
  const allKeys = [...new Set([...Object.keys(beforeAnalysis), ...Object.keys(afterAnalysis)])]

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold mb-4">Metrics Comparison</h3>
      
      <div className="space-y-4">
        {/* Header */}
        <div className="grid grid-cols-4 gap-2 py-2 text-sm font-medium text-gray-500 border-b">
          <div>Metric</div>
          <div className="text-center">Before</div>
          <div className="text-center">After</div>
          <div className="text-center">Status</div>
        </div>

        {/* Metrics Rows */}
        <div className="space-y-1">
          {allKeys.length > 0 ? (
            allKeys.map(key => 
              renderMetricRow(key, beforeAnalysis[key], afterAnalysis[key])
            )
          ) : (
            // Fallback to basic metrics if target_analysis not available
            <>
              {beforeMetrics?.flesch_reading_ease !== undefined && (
                <div className="grid grid-cols-4 gap-2 py-2 text-sm">
                  <div className="font-medium text-gray-700">Reading Ease</div>
                  <div className="text-center">{formatValue(beforeMetrics.flesch_reading_ease)}</div>
                  <div className="text-center">{formatValue(afterMetrics?.flesch_reading_ease || 0)}</div>
                  <div className="text-center">
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
                      N/A
                    </span>
                  </div>
                </div>
              )}
              {beforeMetrics?.avg_sentence_length !== undefined && (
                <div className="grid grid-cols-4 gap-2 py-2 text-sm">
                  <div className="font-medium text-gray-700">Avg Sentence Length</div>
                  <div className="text-center">{formatValue(beforeMetrics.avg_sentence_length)}</div>
                  <div className="text-center">{formatValue(afterMetrics?.avg_sentence_length || 0)}</div>
                  <div className="text-center">
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
                      N/A
                    </span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Summary Stats */}
        <div className="border-t pt-4 mt-4">
          <h4 className="font-medium mb-2">Basic Stats</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Words:</span>
              <span className="ml-2 font-medium">
                {beforeMetrics?.word_count || 0} → {afterMetrics?.word_count || 0}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Sentences:</span>
              <span className="ml-2 font-medium">
                {beforeMetrics?.sentence_count || 0} → {afterMetrics?.sentence_count || 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
