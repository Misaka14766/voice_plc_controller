<template>
  <div class="home-view">
    <el-card class="card-container">
      <template #header>
        <div class="card-header">
          <h2>{{ titleGreeting }}</h2>
          <div class="header-right">
            <div class="tts-toggle">
              <span class="tts-label">语音播报</span>
              <el-switch v-model="ttsEnabled" @change="handleTtsChange" />
            </div>
            <el-tooltip content="PLC连接状态">
              <el-tag :type="plcStatus.connected ? 'success' : 'danger'" class="status-tag">
                {{ plcStatus.connected ? 'PLC已连接' : 'PLC未连接' }}
              </el-tag>
            </el-tooltip>
          </div>
        </div>
      </template>

      <!-- 对话区域 -->
      <div class="chat-container">
        <div class="chat-history" ref="chatHistoryRef">
          <div
            v-for="(message, index) in chatHistory"
            :key="index"
            :class="['message', message.role === 'user' ? 'user-message' : 'assistant-message']"
          >
            <el-avatar
              :size="40"
              :class="['message-avatar', message.role === 'user' ? 'user-avatar' : 'ai-avatar']"
              :src="message.role === 'user' ? userAvatar : undefined"
              @click="message.role === 'user' && showAvatarDialog('user')"
              :style="message.role === 'user' ? { cursor: 'pointer' } : {}"
            >
              <el-icon v-if="message.role === 'assistant'" :size="20"><ElementPlus /></el-icon>
              <el-icon v-else-if="!userAvatar" :size="20"><User /></el-icon>
            </el-avatar>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div v-if="message.template" class="message-tag">
                <el-tag size="small" type="info">模板匹配</el-tag>
              </div>
            </div>
          </div>
          <div v-if="recording" class="message recording-message">
            <el-avatar :size="40" class="recording-avatar">
              <el-icon :size="20"><Mic /></el-icon>
            </el-avatar>
            <div class="message-content">
              <div class="recording-indicator">
                <el-icon class="recording-icon"><Mic /></el-icon>
                <span>正在录音...</span>
                <div class="recording-animation">
                  <div class="dot"></div>
                  <div class="dot"></div>
                  <div class="dot"></div>
                </div>
              </div>
              <div v-if="realTimeSpeechText" class="real-time-speech-text">
                <div class="speech-text-content">{{ realTimeSpeechText }}</div>
                <div class="speech-text-indicator">
                  <el-icon class="pulse-icon"><Mic /></el-icon>
                  <span>识别中...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-container">
          <el-input
            v-model="inputText"
            placeholder="输入指令或按麦克风按钮说话"
            @keyup.enter="sendText"
            class="text-input"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 3 }"
          >
            <template #append>
              <el-button
                type="primary"
                @click="sendText"
                :disabled="!inputText.trim()"
              >
                <el-icon><Promotion /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-button
            :type="recording ? 'danger' : 'success'"
            circle
            @click="toggleRecording"
            class="voice-button"
          >
            <el-icon><Mic /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 快捷指令 -->
      <div class="quick-commands">
        <el-divider content-position="left">
          <span v-if="!editingCommands">快捷指令</span>
          <span v-else>编辑快捷指令</span>
          <el-button
            v-if="!editingCommands"
            type="primary"
            size="small"
            link
            @click="startEditingCommands"
            style="margin-left: 10px"
          >
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
          <template v-else>
            <el-button type="success" size="small" link @click="cancelEditingCommands">
              <el-icon><Check /></el-icon> 完成
            </el-button>
          </template>
        </el-divider>
        <div v-if="editingCommands" class="editing-commands">
          <div v-for="(command, index) in quickCommands" :key="index" class="command-edit-item">
            <template v-if="editingIndex === index">
              <el-input v-model="editingValue" size="small" style="flex: 1" @keyup.enter="saveEditCommand(index)" />
              <el-button type="success" size="small" link @click="saveEditCommand(index)">
                <el-icon><Check /></el-icon>
              </el-button>
              <el-button type="danger" size="small" link @click="cancelEditCommand">
                <el-icon><Close /></el-icon>
              </el-button>
            </template>
            <template v-else>
              <el-tag @click="sendQuickCommand(command)" class="quick-command-tag">{{ command }}</el-tag>
              <el-button type="primary" size="small" link @click="startEditCommand(index)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button type="danger" size="small" link @click="deleteCommand(index)">
                <el-icon><Close /></el-icon>
              </el-button>
            </template>
          </div>
          <div v-if="addingCommand" class="command-edit-item">
            <el-input v-model="newCommandValue" size="small" style="flex: 1" placeholder="输入新指令" @keyup.enter="confirmAddCommand" />
            <el-button type="success" size="small" link @click="confirmAddCommand">
              <el-icon><Check /></el-icon>
            </el-button>
            <el-button type="danger" size="small" link @click="cancelAddCommand">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <el-button v-if="!addingCommand" type="primary" size="small" link @click="startAddCommand" style="margin-top: 10px">
            <el-icon><Plus /></el-icon> 添加新指令
          </el-button>
        </div>
        <div v-else>
          <el-tag
            v-for="command in quickCommands"
            :key="command"
            @click="sendQuickCommand(command)"
            class="quick-command-tag"
          >
            {{ command }}
          </el-tag>
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="system-status">
        <el-divider content-position="left">系统状态</el-divider>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="ASR提供商">{{ plcStatus.asr_provider }}</el-descriptions-item>
          <el-descriptions-item label="TTS提供商">{{ plcStatus.tts_provider }}</el-descriptions-item>
          <el-descriptions-item label="LLM提供商">{{ plcStatus.llm_provider }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 头像预览对话框 -->
    <el-dialog v-model="avatarDialogVisible" title="编辑头像" width="400px" center>
      <div class="avatar-preview-container">
        <el-avatar :size="120" class="preview-avatar" :src="tempAvatar">
          <el-icon v-if="!tempAvatar" :size="40"><User /></el-icon>
        </el-avatar>
      </div>
      <div class="avatar-upload-section">
        <el-upload
          class="avatar-uploader"
          :show-file-list="false"
          :before-upload="beforeAvatarUpload"
          :http-request="handleAvatarUpload"
          accept="image/*"
        >
          <el-button type="primary" size="default">
            <el-icon><Upload /></el-icon> 选择图片
          </el-button>
        </el-upload>
        <p class="upload-hint">支持 JPG、PNG、GIF 格式，建议图片尺寸 200x200</p>
      </div>
      <template #footer>
        <el-button @click="cancelAvatarChange">取消</el-button>
        <el-button type="danger" @click="resetAvatar">恢复默认</el-button>
        <el-button type="primary" @click="confirmAvatarChange">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted, computed } from 'vue'
import { Mic, Plus, Edit, Check, Close, User, ElementPlus, Upload, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { sendChat, synthesizeTTS, healthCheck, getHistory, clearHistory } from '../api'
import { loadQuickCommands, saveQuickCommands } from '../config/quickCommands'

const inputText = ref('')
const chatHistory = ref<any[]>([])
const chatHistoryRef = ref<HTMLElement>()
const recording = ref(false)
const ttsEnabled = ref(true)
const greetingShown = ref(false)
const userAvatar = ref<string>('')
const tempAvatar = ref<string>('')
const avatarDialogVisible = ref(false)
const currentAvatarType = ref<'user' | ''>('')
const realTimeSpeechText = ref('')

const plcStatus = ref({
  connected: false,
  asr_provider: '',
  tts_provider: '',
  llm_provider: ''
})

const quickCommands = ref<string[]>(loadQuickCommands())
const editingCommands = ref(false)
const editingIndex = ref(-1)
const editingValue = ref('')
const addingCommand = ref(false)
const newCommandValue = ref('')

let ws: WebSocket | null = null
let currentAudio: HTMLAudioElement | null = null

const showAvatarDialog = (type: 'user') => {
  currentAvatarType.value = type
  tempAvatar.value = userAvatar.value
  avatarDialogVisible.value = true
}

const beforeAvatarUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB！')
    return false
  }
  return true
}

const handleAvatarUpload = (param: { file: File }) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    tempAvatar.value = e.target?.result as string
  }
  reader.readAsDataURL(param.file)
}

const confirmAvatarChange = () => {
  userAvatar.value = tempAvatar.value
  localStorage.setItem('voice_plc_user_avatar', tempAvatar.value)
  avatarDialogVisible.value = false
  ElMessage.success('头像更新成功')
}

const cancelAvatarChange = () => {
  tempAvatar.value = userAvatar.value
  avatarDialogVisible.value = false
}

const resetAvatar = () => {
  userAvatar.value = ''
  tempAvatar.value = ''
  localStorage.removeItem('voice_plc_user_avatar')
  avatarDialogVisible.value = false
  ElMessage.success('头像已恢复默认')
}

const handleAvatarError = () => {
  userAvatar.value = ''
  localStorage.removeItem('voice_plc_user_avatar')
}

const greetingMessage = computed(() => {
  const hour = new Date().getHours()
  let greeting = ''
  if (hour < 6) greeting = '凌晨好'
  else if (hour < 9) greeting = '早上好'
  else if (hour < 12) greeting = '上午好'
  else if (hour < 14) greeting = '中午好'
  else if (hour < 18) greeting = '下午好'
  else if (hour < 22) greeting = '晚上好'
  else greeting = '夜深了'
  
  return `${greeting}！我是您的工业语音助手。您可以通过语音或文字向我发送指令来控制PLC设备。\n\n我可以帮您：\n• 查询PLC变量状态\n• 控制电机、阀门等设备\n• 查看系统运行参数\n• 以及更多操作...\n\n请选择下方的快捷指令或直接输入您的需求。`
})

const titleGreeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '凌晨好'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

const handleTtsChange = (value: boolean) => {
  localStorage.setItem('voice_plc_tts_enabled', String(value))
  if (!value && currentAudio) {
    currentAudio.pause()
    currentAudio.currentTime = 0
    currentAudio = null
  }
}

const showGreeting = () => {
  if (chatHistory.value.length === 0 && !greetingShown.value) {
    chatHistory.value.push({
      role: 'assistant',
      content: greetingMessage.value,
      template: false
    })
    greetingShown.value = true
    scrollToBottom()
  }
}

// 滚动到聊天记录底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
    }
  })
}

// 发送文本指令
const sendText = async () => {
  const text = inputText.value.trim()
  if (!text) return

  // 添加用户消息
  chatHistory.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  try {
    // 调用API
    const response = await sendChat(text)
    if (response.data) {
      // 添加助手回复
      chatHistory.value.push({
        role: 'assistant',
        content: response.data.response,
        template: response.data.template
      })
      scrollToBottom()

      // 语音合成
      await synthesizeAndPlay(response.data.response)
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    chatHistory.value.push({
      role: 'assistant',
      content: '抱歉，系统出错，请重试'
    })
    scrollToBottom()
  }
}

// 发送快捷指令
const sendQuickCommand = (command: string) => {
  inputText.value = command
  sendText()
}

// 编辑快捷指令
const startEditingCommands = () => {
  editingCommands.value = true
}

const cancelEditingCommands = () => {
  editingCommands.value = false
  editingIndex.value = -1
  addingCommand.value = false
  loadQuickCommandsFromStorage()
}

const startEditCommand = (index: number) => {
  editingIndex.value = index
  editingValue.value = quickCommands.value[index] || ''
}

const saveEditCommand = async (index: number) => {
  const trimmedValue = editingValue.value.trim()
  if (trimmedValue) {
    quickCommands.value[index] = trimmedValue
  }
  editingIndex.value = -1
  await saveCommands()
}

const cancelEditCommand = () => {
  editingIndex.value = -1
}

const startAddCommand = () => {
  addingCommand.value = true
  newCommandValue.value = ''
}

const confirmAddCommand = async () => {
  if (newCommandValue.value.trim()) {
    quickCommands.value.push(newCommandValue.value.trim())
    await saveCommands()
  }
  addingCommand.value = false
  newCommandValue.value = ''
}

const cancelAddCommand = () => {
  addingCommand.value = false
  newCommandValue.value = ''
}

const deleteCommand = async (index: number) => {
  quickCommands.value.splice(index, 1)
  await saveCommands()
}

const saveCommands = () => {
  try {
    saveQuickCommands(quickCommands.value)
  } catch (error) {
    console.error('保存快捷指令失败:', error)
  }
}

// 加载快捷指令
const loadQuickCommandsFromStorage = () => {
  quickCommands.value = loadQuickCommands()
}

// 在组件顶层或 script setup 中需要声明这些变量以保存音频实例
let audioContext: AudioContext | null = null
let audioWorkletNode: AudioWorkletNode | null = null
let mediaStream: MediaStream | null = null
// 扩展Window接口以支持webkitAudioContext
interface Window {
  webkitAudioContext?: typeof AudioContext
}
// 注：假设 ws 和 recording 已经在你的代码作用域内声明了

// 开始录音
const startRecording = async () => {
  if (recording.value) return

  try {
    // --- 1. 连接WebSocket (保留你原有的完整逻辑) ---
    const wsUrl = import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') + '/ws/asr'
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket连接已打开')
    }

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'partial') {
        // 更新实时识别文本
        realTimeSpeechText.value = data.text
        console.log('实时识别:', data.text)
      } else if (data.type === 'final') {
        // 清空实时识别文本
        realTimeSpeechText.value = ''
        
        if (data.text) {
          // 将最终识别结果添加到对话历史
          chatHistory.value.push({ role: 'user', content: data.text })
          scrollToBottom()

          try {
            // 调用对话接口
            const response = await sendChat(data.text)
            if (response.data) {
              chatHistory.value.push({
                role: 'assistant',
                content: response.data.response,
                template: response.data.template
              })
              scrollToBottom()
              await synthesizeAndPlay(response.data.response)
            }
          } catch (error) {
            console.error('发送消息失败:', error)
            chatHistory.value.push({
              role: 'assistant',
              content: '抱歉，系统出错，请重试'
            })
            scrollToBottom()
          }
        }
        // 不要自动关闭WebSocket连接，保持连接以便下次使用
      } else if (data.type === 'error') {
        console.error('WebSocket错误:', data.text)
        ElMessage.error(data.text)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      ElMessage.error('语音识别服务连接失败')
      // 发生错误时重置录音状态，但不调用stopRecording避免循环错误
      recording.value = false
      cleanupAudioResources()
    }

    ws.onclose = () => {
      console.log('WebSocket连接已关闭')
      // 连接关闭时重置UI状态，但不调用stopRecording避免循环错误
      recording.value = false
      cleanupAudioResources()
    }

    // 等待WebSocket连接建立
    await new Promise((resolve, reject) => {
      const timer = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          clearInterval(timer)
          resolve(null)
        } else if (ws?.readyState === WebSocket.CLOSED || ws?.readyState === WebSocket.CLOSING) {
          clearInterval(timer)
          reject(new Error('WebSocket连接失败'))
        }
      }, 100)
    })

    // --- 2. 核心重构：使用 Audio Worklet 处理音频 ---
    
    // 获取麦克风权限
    mediaStream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        channelCount: 1, // 单声道
        echoCancellation: true,
        noiseSuppression: true
      }
    })
    
    // 初始化 AudioContext
    audioContext = new AudioContext({sampleRate: 16000})
    console.log('AudioContext采样率:', audioContext.sampleRate)
    
    // 检查Audio Worklet支持
    if (!audioContext.audioWorklet) {
      throw new Error('浏览器不支持Audio Worklet，请使用现代浏览器如Chrome、Edge、Firefox等')
    }

    // 添加Audio Worklet模块
    await audioContext.audioWorklet.addModule('/audio-worklet-processor.js')
    console.log('Audio Worklet模块加载成功')
    
    // 创建音频源节点
    const source = audioContext.createMediaStreamSource(mediaStream)
    
    // 创建Audio Worklet节点
    audioWorkletNode = new AudioWorkletNode(audioContext, 'audio-worklet-processor', {
      numberOfInputs: 1,
      numberOfOutputs: 1,
      outputChannelCount: [1],
      processorOptions: {
        frameSize: 128 // 每帧处理128个样本
      }
    })

    // 设置Audio Worklet消息处理器
    audioWorkletNode.port.onmessage = (event) => {
      const { type, data } = event.data
      
      if (type === 'audioData' && ws?.readyState === WebSocket.OPEN) {
        // 通过WebSocket发送PCM数据
        ws.send(data)
      }
    }

    // 连接音频处理图
    source.connect(audioWorkletNode)
    // 连接到destination以保持音频处理活跃
    audioWorkletNode.connect(audioContext.destination)

    // 通知Audio Worklet开始处理（只发送连接状态，不传递WebSocket对象）
    audioWorkletNode.port.postMessage({
      type: 'connect'
    })

    recording.value = true
    console.log('Audio Worklet录音已启动')

  } catch (error) {
    console.error('录音失败:', error)
    const errorMessage = error instanceof Error ? error.message : '录音权限被拒绝或设备不可用'
    ElMessage.error(errorMessage)
    if (ws) ws.close()
    recording.value = false
  }
}

// 清理音频资源（不发送结束标记）
const cleanupAudioResources = async () => {
  // 1. 通知Audio Worklet停止处理
  if (audioWorkletNode) {
    audioWorkletNode.port.postMessage({
      type: 'disconnect'
    })
    audioWorkletNode.disconnect()
    audioWorkletNode = null
  }
  
  // 2. 关闭 AudioContext
  if (audioContext && audioContext.state !== 'closed') {
    await audioContext.close()
    audioContext = null
  }

  // 3. 停止并释放麦克风硬件流
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }

  console.log('音频资源已清理')
}

// 停止录音
const stopRecording = async () => {
  if (!recording.value) return

  recording.value = false

  // 1. 发送结束标记给后端
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(new ArrayBuffer(0))
  }

  // 2. 清理音频资源
  await cleanupAudioResources()

  // 3. 清空实时识别文本
  realTimeSpeechText.value = ''

  console.log('Audio Worklet录音已停止')
}

// 单击切换录音状态 (保持不变)
const toggleRecording = () => {
  if (recording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}



// 文本转语音并播放
const synthesizeAndPlay = async (text: string) => {
  if (!ttsEnabled.value) return
  try {
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      currentAudio = null
    }
    const response = await synthesizeTTS(text)
    if (response.data && response.data.audio) {
      currentAudio = new Audio(`data:audio/mp3;base64,${response.data.audio}`)
      currentAudio.play()
    }
  } catch (error) {
    console.error('语音合成失败:', error)
  }
}

// 获取系统状态
const getSystemStatus = async () => {
  try {
    const response = await healthCheck()
    if (response.data) {
      plcStatus.value = {
        connected: response.data.plc_connected,
        asr_provider: response.data.asr_provider,
        tts_provider: response.data.tts_provider,
        llm_provider: response.data.llm_provider
      }
    }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  }
}

// 获取对话历史
const loadHistory = async () => {
  try {
    const response = await getHistory()
    if (response.data && response.data.history) {
      chatHistory.value = response.data.history
      scrollToBottom()
    }
  } catch (error) {
    console.error('获取对话历史失败:', error)
  }
}

// 组件挂载时初始化
onMounted(() => {
  const savedTts = localStorage.getItem('voice_plc_tts_enabled')
  if (savedTts !== null) {
    ttsEnabled.value = savedTts === 'true'
  }
  const savedAvatar = localStorage.getItem('voice_plc_user_avatar')
  if (savedAvatar) {
    userAvatar.value = savedAvatar
  }
  getSystemStatus()
  loadHistory().then(() => {
    showGreeting()
  })
  loadQuickCommandsFromStorage()
  setInterval(getSystemStatus, 10000)
})

// 组件卸载时清理
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.home-view {
  padding: 20px;
}

.card-container {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.tts-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f5f7fa;
  padding: 6px 12px;
  border-radius: 20px;
}

.tts-label {
  font-size: 13px;
  color: #606266;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.status-tag {
  margin-left: 10px;
}

.chat-container {
  margin-top: 20px;
}

.chat-history {
  height: 400px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  background-color: #f9f9f9;
}

.message {
  display: flex;
  margin-bottom: 15px;
  animation: fadeIn 0.3s ease-in-out;
  gap: 2px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.user-message .message-avatar {
  flex-shrink: 0;
}

.user-avatar {
  cursor: pointer;
  transition: transform 0.2s;
}

.user-avatar:hover {
  transform: scale(1.1);
}

.ai-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.recording-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-preview-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.preview-avatar {
  border: 3px solid #e4e7ed;
}

.avatar-upload-section {
  text-align: center;
  padding: 10px 0;
}

.avatar-uploader {
  margin-bottom: 10px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin: 8px 0 0 0;
}

.message-content {
  flex: 0 1 auto;
  max-width: 75%;
}

.user-message .message-content {
  text-align: right;
}

.message-text {
  padding: 10px 15px;
  border-radius: 18px;
  line-height: 1.4;
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  display: inline-block;
  text-align: left;
}

.user-message .message-text {
  text-align: right;
  background-color: #409eff;
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant-message .message-text {
  background-color: white;
  color: #303133;
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 4px;
}

.message-tag {
  margin-top: 5px;
}

.recording-message {
  align-items: center;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  background-color: #f0f9ff;
  border: 1px solid #e1f5fe;
  border-radius: 18px;
  color: #0288d1;
}

.recording-icon {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.recording-animation {
  display: flex;
  gap: 5px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #0288d1;
  animation: bounce 1.5s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.input-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.text-input {
  flex: 1;
}

.voice-button {
  width: 50px;
  height: 50px;
}

.quick-commands {
  margin-top: 30px;
}

.quick-command-tag {
  margin: 5px;
  cursor: pointer;
  transition: all 0.3s;
}

.quick-command-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.editing-commands {
  padding: 10px 0;
}

.command-edit-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.command-edit-item .el-tag {
  margin: 0;
}

.system-status {
  margin-top: 30px;
}

/* 实时语音识别文本样式 */
.real-time-speech-text {
  margin-top: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  border: 1px solid #bbdefb;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.1);
}

.speech-text-content {
  font-size: 16px;
  font-weight: 500;
  color: #1565c0;
  margin-bottom: 8px;
  line-height: 1.4;
}

.speech-text-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #5c6bc0;
}

.pulse-icon {
  animation: pulse 1.5s infinite;
}

/* 滚动条样式 */
.chat-history::-webkit-scrollbar {
  width: 8px;
}

.chat-history::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.chat-history::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.chat-history::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
