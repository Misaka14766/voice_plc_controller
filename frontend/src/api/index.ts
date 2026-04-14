import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
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
}

// 对话接口
export const sendChat = (text: string) =>
  api.post<ChatResponse>('/api/chat', { text })

// PLC接口
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

// TTS接口
export const synthesizeTTS = (text: string) =>
  api.post<{ audio: string }>('/api/tts', { text })

// 清空历史
export const clearHistory = () =>
  api.post<{ success: boolean }>('/api/clear')

// 健康检查
export const healthCheck = () =>
  api.get<HealthResponse>('/api/health')

// 系统状态
export const getStatus = () =>
  api.get<SystemStatus>('/api/status')

// 对话历史
export const getHistory = () =>
  api.get<HistoryResponse>('/api/history')

// 配置查询
export const getConfig = () =>
  api.get<ConfigResponse>('/api/config')

