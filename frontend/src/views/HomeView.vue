<template>
  <div class="home-view">
    <el-card class="card-container">
      <template #header>
        <div class="card-header">
          <h2>语音PLC控制</h2>
          <div class="status-indicators">
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
            <div class="message-avatar">
              <el-avatar :size="40">
                {{ message.role === 'user' ? '我' : 'AI' }}
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div v-if="message.template" class="message-tag">
                <el-tag size="small" type="info">模板匹配</el-tag>
              </div>
            </div>
          </div>
          <div v-if="recording" class="message recording-message">
            <div class="message-avatar">
              <el-avatar :size="40" icon="Mic" />
            </div>
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
          >
            <template #append>
              <el-button
                type="primary"
                @click="sendText"
                :disabled="!inputText.trim()"
              >
                <el-icon><PaperPlane /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-button
            :type="recording ? 'danger' : 'success'"
            circle
            @mousedown="startRecording"
            @mouseup="stopRecording"
            @touchstart="startRecording"
            @touchend="stopRecording"
            class="voice-button"
          >
            <el-icon><Mic /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 快捷指令 -->
      <div class="quick-commands">
        <el-divider content-position="left">快捷指令</el-divider>
        <el-tag
          v-for="command in quickCommands"
          :key="command"
          @click="sendQuickCommand(command)"
          class="quick-command-tag"
        >
          {{ command }}
        </el-tag>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { Mic } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { sendChat, synthesizeTTS, healthCheck, getHistory, clearHistory } from '../api'

const inputText = ref('')
const chatHistory = ref<any[]>([])
const chatHistoryRef = ref<HTMLElement>()
const recording = ref(false)
const plcStatus = ref({
  connected: false,
  asr_provider: '',
  tts_provider: '',
  llm_provider: ''
})

const quickCommands = [
  '启动电机',
  '停止电机',
  '查看温度',
  '设置温度为25度',
  '查看压力',
  'PLC状态'
]

// WebSocket连接
let ws: WebSocket | null = null
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []

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

// 开始录音
const startRecording = async () => {
  if (recording.value) return

  try {
    // 连接WebSocket
    const wsUrl = import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') + '/ws/asr'
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket连接已打开')
    }

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'partial') {
        // 收到部分识别结果，可以实时显示
        console.log('实时识别:', data.text)
      } else if (data.type === 'final') {
        // 收到最终识别结果
        if (data.text) {
          chatHistory.value.push({ role: 'user', content: data.text })
          scrollToBottom()

          // 发送文本指令
          try {
            const response = await sendChat(data.text)
            if (response.data) {
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
        ws?.close()
      } else if (data.type === 'error') {
        console.error('WebSocket错误:', data.text)
        ElMessage.error(data.text)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      ElMessage.error('语音识别服务连接失败')
      recording.value = false
    }

    ws.onclose = () => {
      console.log('WebSocket连接已关闭')
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

    // 获取麦克风权限并开始录音
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && ws?.readyState === WebSocket.OPEN) {
        // 实时发送音频数据
        const reader = new FileReader()
        reader.onload = (e) => {
          const audioData = e.target?.result as ArrayBuffer
          const base64Data = btoa(String.fromCharCode(...new Uint8Array(audioData)))
          
          ws?.send(JSON.stringify({
            type: 'audio',
            data: base64Data,
            is_final: false
          }))
        }
        reader.readAsArrayBuffer(event.data)
      }
    }

    mediaRecorder.start(100) // 每100ms发送一次数据
    recording.value = true
  } catch (error) {
    console.error('录音失败:', error)
    ElMessage.error('录音权限被拒绝或设备不可用')
    if (ws) {
      ws.close()
    }
  }
}

// 停止录音
const stopRecording = async () => {
  if (!recording.value || !mediaRecorder) return

  recording.value = false
  mediaRecorder.stop()

  mediaRecorder.onstop = async () => {
    // 发送最终音频数据标记
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'audio',
        data: '',
        is_final: true
      }))
    }

    // 停止媒体流
    const stream = mediaRecorder?.stream
    stream?.getTracks().forEach(track => track.stop())
  }
}

// 文本转语音并播放
const synthesizeAndPlay = async (text: string) => {
  try {
    const response = await synthesizeTTS(text)
    if (response.data && response.data.audio) {
      const audio = new Audio(`data:audio/mp3;base64,${response.data.audio}`)
      audio.play()
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
  getSystemStatus()
  loadHistory()
  // 每10秒更新一次系统状态
  setInterval(getSystemStatus, 10000)
})

// 组件卸载时清理
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  if (mediaRecorder) {
    mediaRecorder.stop()
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
  margin: 0 10px;
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.user-message .message-content {
  text-align: right;
}

.message-text {
  padding: 10px 15px;
  border-radius: 18px;
  line-height: 1.4;
}

.user-message .message-text {
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

.system-status {
  margin-top: 30px;
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
