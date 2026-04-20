export const DEFAULT_QUICK_COMMANDS = [
  '启动电机',
  '停止电机',
  '查看温度',
  '设置温度为25度',
  '查看压力',
  'PLC状态',
  '查看水位'
]

const STORAGE_KEY = 'voice_plc_quick_commands'

export const loadQuickCommands = (): string[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error('加载快捷指令失败:', e)
  }
  return [...DEFAULT_QUICK_COMMANDS]
}

export const saveQuickCommands = (commands: string[]): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(commands))
  } catch (e) {
    console.error('保存快捷指令失败:', e)
  }
}

export const resetQuickCommands = (): string[] => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (e) {
    console.error('重置快捷指令失败:', e)
  }
  return [...DEFAULT_QUICK_COMMANDS]
}