<template>
  <div class="config-view">
    <el-card class="card-container">
      <template #header>
        <div class="card-header">
          <h2>配置管理</h2>
          <el-button type="primary" @click="refreshConfig" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新配置
          </el-button>
        </div>
      </template>

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>

      <div v-else class="config-container">
        <el-tabs type="border-card">
          <el-tab-pane label="系统配置">
            <el-form :model="config" label-width="120px" class="config-form">
              <el-form-item label="ASR提供商">
                <el-select v-model="config.asr_provider" disabled>
                  <el-option label="阿里云" value="aliyun" />
                  <el-option label="FunASR" value="funasr" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="TTS提供商">
                <el-select v-model="config.tts_provider" disabled>
                  <el-option label="Edge TTS" value="edge" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="LLM提供商">
                <el-select v-model="config.llm_provider" disabled>
                  <el-option label="OpenAI" value="openai" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="PLC启用">
                <el-switch v-model="config.plc_enabled" disabled />
              </el-form-item>
              
              <el-form-item label="模板匹配">
                <el-switch v-model="config.template_matching" disabled />
              </el-form-item>
              
              <el-form-item label="语音输入">
                <el-switch v-model="config.voice_input_enabled" disabled />
              </el-form-item>
              
              <el-form-item label="语音输出">
                <el-switch v-model="config.voice_output_enabled" disabled />
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="连接状态">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="PLC连接">
                <el-tag :type="plcStatus.connected ? 'success' : 'danger'">
                  {{ plcStatus.connected ? '已连接' : '未连接' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="ASR提供商">
                {{ plcStatus.asr_provider }}
              </el-descriptions-item>
              <el-descriptions-item label="TTS提供商">
                {{ plcStatus.tts_provider }}
              </el-descriptions-item>
              <el-descriptions-item label="LLM提供商">
                {{ plcStatus.llm_provider }}
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="系统信息">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="系统版本">
                1.0.0
              </el-descriptions-item>
              <el-descriptions-item label="API地址">
                {{ apiBaseUrl }}
              </el-descriptions-item>
              <el-descriptions-item label="前端版本">
                {{ frontendVersion }}
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
        </el-tabs>

        <div class="config-note">
          <el-alert
            title="配置说明"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>当前配置为只读模式，如需修改配置请编辑后端 .env 文件。</p>
              <p>修改配置后需要重启后端服务才能生效。</p>
            </template>
          </el-alert>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getConfig, healthCheck } from '../api'

const loading = ref(true)
const config = ref({
  asr_provider: '',
  tts_provider: '',
  llm_provider: '',
  plc_enabled: false,
  template_matching: false,
  voice_input_enabled: false,
  voice_output_enabled: false
})

const plcStatus = ref({
  connected: false,
  asr_provider: '',
  tts_provider: '',
  llm_provider: ''
})

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const frontendVersion = '1.0.0'

// 刷新配置
const refreshConfig = async () => {
  loading.value = true
  try {
    // 获取系统配置
    const configResponse = await getConfig()
    if (configResponse.data) {
      config.value = configResponse.data
    }

    // 获取系统状态
    const healthResponse = await healthCheck()
    if (healthResponse.data) {
      plcStatus.value = {
        connected: healthResponse.data.plc_connected,
        asr_provider: healthResponse.data.asr_provider,
        tts_provider: healthResponse.data.tts_provider,
        llm_provider: healthResponse.data.llm_provider
      }
    }
  } catch (error) {
    console.error('获取配置失败:', error)
  } finally {
    loading.value = false
  }
}

// 组件挂载时刷新配置
onMounted(() => {
  refreshConfig()
})
</script>

<style scoped>
.config-view {
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

.loading-state {
  padding: 20px 0;
}

.config-container {
  margin-top: 20px;
}

.config-form {
  margin-top: 20px;
}

.config-note {
  margin-top: 30px;
}
</style>
