import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
  paramsSerializer: (params) => {
    const searchParams = new URLSearchParams()
    for (const key in params) {
      const value = params[key]
      if (Array.isArray(value)) {
        value.forEach(item => searchParams.append(key, item))
      } else {
        searchParams.append(key, value)
      }
    }
    return searchParams.toString()
  }
})

export interface ChatResponse {
  response: string
  template: boolean
}

export interface PLCReadRequest {
  variable: string
  data_type?: string
}

export interface PLCWriteRequest {
  variable: string
  value: string | number | boolean
  data_type?: string
}

export interface PLCVariable {
  name: string
  type: string
  comment?: string
  unit?: string
  min?: number
  max?: number
}

export interface HealthResponse {
  status: string
  plc_connected: boolean
  asr_provider: string
  tts_provider: string
  llm_provider: string
}

export interface SystemStatus {
  plc_connected: boolean
  asr_provider: string
  tts_provider: string
  llm_provider: string
  template_matching: boolean
}

export interface SystemMetrics {
  cpu: number
  memory: number
  network: number
  uptime: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  template?: boolean
}

export interface HistoryResponse {
  history: ChatMessage[]
}

export interface ConfigResponse {
  asr_provider: string
  tts_provider: string
  llm_provider: string
  plc_enabled: boolean
  template_matching: boolean
  voice_input_enabled: boolean
  voice_output_enabled: boolean
  db_enabled?: boolean
  db_type?: string
  data_collection_enabled?: boolean
}

export interface RealtimeDataItem {
  name: string
  value: number | null
  timestamp?: string
  unit?: string
}

export interface ChartDataResponse {
  success: boolean
  data: Array<{
    timestamp: string
    value: number
    variable_name?: string
    data_type?: string
  }>
  count?: number
  aggregation?: string
  time_range?: string
}

export interface CollectorStatusResponse {
  success: boolean
  running: boolean
  interval_ms?: number
  variables_count?: number
  buffer_size?: number
  batch_size?: number
  variables?: string[]
  message?: string
}

export const sendChat = (text: string) =>
  api.post<ChatResponse>('/api/chat', { text })

export const readPLC = (variable: string, dataType: string = 'INT') =>
  api.post<{ success: boolean; value?: any; error?: string }>('/api/plc/read', {
    variable,
    data_type: dataType
  })

export const writePLC = (variable: string, value: any, dataType: string = 'INT') =>
  api.post<{ success: boolean; error?: string }>('/api/plc/write', {
    variable,
    value,
    data_type: dataType
  })

export const listPLCVariables = () =>
  api.get<{ success: boolean; variables: PLCVariable[]; error?: string }>('/api/plc/variables')

export const synthesizeTTS = (text: string) =>
  api.post<{ audio: string }>('/api/tts', { text })

export const clearHistory = () =>
  api.post<{ success: boolean }>('/api/clear')

export const healthCheck = () =>
  api.get<HealthResponse>('/api/health')

export const getStatus = () =>
  api.get<SystemStatus>('/api/status')

export const getHistory = () =>
  api.get<HistoryResponse>('/api/history')

export const getConfig = () =>
  api.get<ConfigResponse>('/api/config')

export const updateConfig = (config: any) =>
  api.post<{ success: boolean; message: string }>('/api/config', config)

export const getRealtimeData = (variables: string[]) =>
  api.get<{ success: boolean; data: RealtimeDataItem[] }>('/api/data/realtime', {
    params: { variables }
  })

export const getMonitorVariables = () =>
  api.get<{ success: boolean; variables: Array<[string, string]> }>('/api/plc/monitor-variables')

export interface MonitorVariable {
  name: string
  type: string
}

export const updateMonitorVariables = (variables: MonitorVariable[]) =>
  api.post<{ success: boolean; message: string; variables: MonitorVariable[] }>('/api/plc/monitor-variables', {
    variables
  })

export const getHistoryData = (
  variable: string,
  hours: number = 1,
  aggregation: string = 'mean'
) =>
  api.get<{ success: boolean; data: any[]; count: number }>('/api/data/history', {
    params: { variable, hours, aggregation }
  })

export const getChartData = (
  variable: string,
  timeRange: string = '1h',
  aggregation: string = 'mean'
) =>
  api.get<ChartDataResponse>('/api/data/chart', {
    params: { variable, time_range: timeRange, aggregation }
  })

export const getCollectorStatus = () =>
  api.get<CollectorStatusResponse>('/api/collector/status')

export const startCollector = () =>
  api.post<{ success: boolean; message: string }>('/api/collector/start')

export const stopCollector = () =>
  api.post<{ success: boolean; message: string }>('/api/collector/stop')

export const getPLCDeviceInfo = () =>
  api.get<{ success: boolean; model?: string; system?: string; ipAddress?: string; status?: string; modelLink?: string; systemLink?: string; imageUrl?: string }>('/api/plc/device-info')

export const readPLCList = (variables: string[]) =>
  api.post<{ success: boolean; values: Record<string, any> }>('/api/plc/read-list', { variables })

export const writePLCList = (variables: Record<string, any>) =>
  api.post<{ success: boolean; results: Record<string, string> }>('/api/plc/write-list', { variables })

export const clearVariableDataAPI = (variable: string) =>
  api.post<{ success: boolean; message: string }>('/api/db/clear-variable', {}, { params: { variable } })

export const clearAllDataAPI = () =>
  api.post<{ success: boolean; message: string }>('/api/db/clear-all')

export const getQuickCommands = () =>
  api.get<{ success: boolean; commands: string[] }>('/api/quick-commands')

export const saveQuickCommands = (commands: string[]) =>
  api.post<{ success: boolean; message: string }>('/api/quick-commands', { commands })

export const getSystemMetrics = () =>
  api.get<SystemMetrics>('/api/system/metrics')