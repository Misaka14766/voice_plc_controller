export interface ModelMapping {
  variable: string
  label: string
}

export const MODEL_COMPONENT_MAPPINGS: Record<string, ModelMapping> = {
  Mesh149: { variable: 'MAIN.WaterLevel', label: '水箱1水位' },
  Mesh153: { variable: 'MAIN.WaterLevel2', label: '水箱2水位' },
  Mesh185: { variable: 'MAIN.Temperature', label: '加热器温度' }
}