<template>
  <div class="config-view">
    <el-card class="card-container">
      <template #header>
        <div class="card-header">
          <h2>配置管理</h2>
          <div class="header-actions">
            <el-button type="primary" @click="refreshConfig" :loading="loading">
              <el-icon><Refresh /></el-icon> 刷新配置
            </el-button>
            <el-button type="success" @click="saveConfig" :loading="saving" :disabled="!isModified">
              <el-icon><Check /></el-icon> 保存配置
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="15" animated />
      </div>

      <div v-else class="config-container">
        <el-tabs type="border-card">
          <el-tab-pane label="监控配置">
            <el-form :model="config.monitor" label-width="150px" class="config-form">
              <el-form-item label="监控变量">
                <el-input
                  v-model="config.monitor.variables"
                  type="textarea"
                  :rows="3"
                  placeholder="格式: MAIN.WaterLevel:REAL, MAIN.Temperature:REAL"
                  @input="handleConfigChange"
                />
                <div class="form-hint">变量名:类型，多个变量用逗号分隔</div>
              </el-form-item>
              
              <el-form-item label="监控间隔 (毫秒)">
                <el-input-number
                  v-model="config.monitor.interval_ms"
                  :min="100"
                  :max="10000"
                  :step="100"
                  @change="handleConfigChange"
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="数据采集配置">
            <el-form :model="config.data_collection" label-width="150px" class="config-form">
              <el-form-item label="启用数据采集">
                <el-switch
                  v-model="config.data_collection.enabled"
                  @change="handleConfigChange"
                />
              </el-form-item>
              
              <el-form-item label="采集间隔 (毫秒)">
                <el-input-number
                  v-model="config.data_collection.interval"
                  :min="100"
                  :max="10000"
                  :step="100"
                  @change="handleConfigChange"
                />
              </el-form-item>
              
              <el-form-item label="批量写入大小">
                <el-input-number
                  v-model="config.data_collection.batch_size"
                  :min="1"
                  :max="100"
                  :step="1"
                  @change="handleConfigChange"
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="交互配置">
            <el-form :model="config.interaction" label-width="150px" class="config-form">
              <el-form-item label="启用语音输入">
                <el-switch
                  v-model="config.interaction.voice_input_enabled"
                  @change="handleConfigChange"
                />
              </el-form-item>
              
              <el-form-item label="启用语音输出">
                <el-switch
                  v-model="config.interaction.voice_output_enabled"
                  @change="handleConfigChange"
                />
              </el-form-item>
              
              <el-form-item label="使用模板匹配">
                <el-switch
                  v-model="config.interaction.use_template_matching"
                  @change="handleConfigChange"
                />
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="PLC配置">
            <el-form :model="config.plc" label-width="150px" class="config-form">
              <el-form-item label="触发变量">
                <el-input
                  v-model="config.plc.trigger_var"
                  placeholder="例如: MAIN.bVoiceTrigger"
                  @input="handleConfigChange"
                />
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

        <div v-if="isModified" class="config-note">
          <el-alert
            title="配置已修改"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>您已经修改了配置，请点击保存按钮使配置生效。</p>
            </template>
          </el-alert>
        </div>
        
        <div v-else class="config-note">
          <el-alert
            title="配置说明"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>配置修改后会立即生效，无需重启服务。</p>
              <p>配置会持久化到后端配置文件中。</p>
            </template>
          </el-alert>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { Refresh, Check } from '@element-plus/icons-vue'
import { getConfig, updateConfig, healthCheck } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(true)
const saving = ref(false)
const isModified = ref(false)
const originalConfig = ref({})

const config = reactive({
  monitor: {
    variables: '',
    interval_ms: 1000
  },
  data_collection: {
    enabled: true,
    interval: 1000,
    batch_size: 10
  },
  interaction: {
    voice_input_enabled: true,
    voice_output_enabled: true,
    use_template_matching: true
  },
  plc: {
    trigger_var: ''
  }
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
      Object.assign(config, configResponse.data)
      originalConfig.value = JSON.parse(JSON.stringify(config))
      isModified.value = false
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
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  saving.value = true
  try {
    const response = await updateConfig(config)
    if (response.data.success) {
      ElMessage.success('配置保存成功')
      originalConfig.value = JSON.parse(JSON.stringify(config))
      isModified.value = false
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 处理配置变化
const handleConfigChange = () => {
  isModified.value = JSON.stringify(config) !== JSON.stringify(originalConfig.value)
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
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
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

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.config-note {
  margin-top: 30px;
}
</style>
