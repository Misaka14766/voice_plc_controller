<template>
  <div class="database-view">
    <el-card class="db-header-card">
      <template #header>
        <div class="header-content">
          <span class="header-title">数据库管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="refreshDBStatus">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
            <el-button :type="dbStatus.connected ? 'success' : 'danger'" disabled>
              <el-icon v-if="dbStatus.connected"><Check /></el-icon>
              <el-icon v-else><Close /></el-icon>
              {{ dbStatus.connected ? '已连接' : '未连接' }}
            </el-button>
          </div>
        </div>
      </template>
      <div class="db-status-info">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="status-item">
              <span class="status-label">数据库类型:</span>
              <span class="status-value">{{ dbStatus.dbType || '未知' }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <span class="status-label">连接状态:</span>
              <span class="status-value" :class="dbStatus.connected ? 'status-success' : 'status-error'">
                {{ dbStatus.connected ? '已连接' : '未连接' }}
              </span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <span class="status-label">数据采集:</span>
              <span class="status-value" :class="dbStatus.collectorRunning ? 'status-success' : 'status-warning'">
                {{ dbStatus.collectorRunning ? '运行中' : '已停止' }}
              </span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <span class="status-label">变量数量:</span>
              <span class="status-value">{{ dbStatus.variablesCount || 0 }}</span>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" class="mt-4">
      <el-tab-pane label="数据管理" name="data-management">
        <div class="data-management">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>PLC 变量数据</span>
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索变量"
                  style="width: 300px"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </div>
            </template>
            <el-table :data="filteredVariables" style="width: 100%">
              <el-table-column prop="name" label="变量名" width="200" />
              <el-table-column prop="value" label="当前值" width="120">
                <template #default="scope">
                  <span :class="getValueClass(scope.row)">{{ formatValue(scope.row.value) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="unit" label="单位" width="100" />
              <el-table-column prop="comment" label="描述" />
              <el-table-column prop="min" label="最小值" width="100" />
              <el-table-column prop="max" label="最大值" width="100" />
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="scope">
                  <el-button type="primary" size="small" @click="showVariableHistory(scope.row)">
                    历史
                  </el-button>
                  <el-button type="warning" size="small" @click="showVariableDetails(scope.row)">
                    详情
                  </el-button>
                  <el-button type="danger" size="small" @click="clearVariableData(scope.row)">
                    清空
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="历史数据" name="history-data">
        <div class="history-data">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>历史数据查询</span>
                <el-select v-model="selectedHistoryVariable" placeholder="选择变量">
                  <el-option
                    v-for="variable in variables"
                    :key="variable.name"
                    :label="variable.comment || variable.name"
                    :value="variable.name"
                  />
                </el-select>
              </div>
            </template>
            <div class="history-controls">
              <el-select v-model="historyHours" placeholder="时间范围" style="width: 120px">
                <el-option label="1小时" :value="1" />
                <el-option label="6小时" :value="6" />
                <el-option label="12小时" :value="12" />
                <el-option label="24小时" :value="24" />
              </el-select>
              <el-select v-model="historyAggregation" placeholder="聚合方式" style="width: 120px">
                <el-option label="平均值" value="mean" />
                <el-option label="最大值" value="max" />
                <el-option label="最小值" value="min" />
                <el-option label="总和" value="sum" />
              </el-select>
              <el-button type="primary" @click="loadHistoryData">
                查询
              </el-button>
            </div>
            <div v-if="historyData.length > 0" class="chart-container">
              <div ref="chartRef" class="chart"></div>
            </div>
            <div v-else class="empty-history">
              <el-icon :size="48"><Coin /></el-icon>
              <p>暂无历史数据</p>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="系统管理" name="system-management">
        <div class="system-management">
          <el-card>
            <template #header>
              <span>数据库系统管理</span>
            </template>
            <el-form :model="systemForm" label-width="120px">
              <el-form-item label="数据采集">
                <el-switch v-model="systemForm.collectorEnabled" @change="toggleCollector" />
              </el-form-item>
              <el-form-item label="采集间隔(ms)">
                <el-input-number v-model="systemForm.collectorInterval" :min="100" :max="60000" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveSystemSettings">
                  保存设置
                </el-button>
                <el-button @click="clearDatabase">
                  清空数据库
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 变量详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentVariable?.comment || currentVariable?.name || '变量详情'"
      width="600px"
    >
      <div v-if="currentVariable" class="variable-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="变量名">{{ currentVariable.name }}</el-descriptions-item>
          <el-descriptions-item label="当前值">{{ formatValue(currentVariable.value) }} {{ currentVariable.unit || '' }}</el-descriptions-item>
          <el-descriptions-item label="数据类型">{{ currentVariable.type || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentVariable.comment || '无' }}</el-descriptions-item>
          <el-descriptions-item label="单位">{{ currentVariable.unit || '无' }}</el-descriptions-item>
          <el-descriptions-item label="取值范围">{{ currentVariable.min || 0 }} - {{ currentVariable.max || 100 }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 历史数据对话框 -->
    <el-dialog
      v-model="historyDialogVisible"
      :title="`${currentVariable?.comment || currentVariable?.name} 历史数据`"
      width="800px"
      height="600px"
    >
      <div v-if="currentVariable" class="history-dialog-content">
        <div class="history-dialog-controls">
          <el-select v-model="dialogHistoryHours" placeholder="时间范围" style="width: 120px">
            <el-option label="1小时" :value="1" />
            <el-option label="6小时" :value="6" />
            <el-option label="12小时" :value="12" />
            <el-option label="24小时" :value="24" />
          </el-select>
          <el-button type="primary" @click="loadDialogHistoryData">
            刷新
          </el-button>
        </div>
        <div ref="historyChartRef" class="history-chart"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, Check, Close, Coin } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getConfig, getMonitorVariables, getRealtimeData, getCollectorStatus, startCollector, stopCollector, getHistoryData, clearVariableDataAPI, clearAllDataAPI } from '../api'

const activeTab = ref('data-management')
const searchKeyword = ref('')
const selectedHistoryVariable = ref('')
const historyHours = ref(1)
const historyAggregation = ref('mean')
const dialogHistoryHours = ref(1)

const dbStatus = ref({
  connected: false,
  dbType: '',
  collectorRunning: false,
  variablesCount: 0
})

const variables = ref<any[]>([])
const realtimeData = ref<any[]>([])
const historyData = ref<any[]>([])
const filteredVariables = ref<any[]>([])

const systemForm = ref({
  collectorEnabled: false,
  collectorInterval: 2000
})

const detailDialogVisible = ref(false)
const historyDialogVisible = ref(false)
const currentVariable = ref<any>(null)

const chartRef = ref<HTMLElement | null>(null)
const historyChartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null
let historyChart: echarts.ECharts | null = null

const formatValue = (value: any) => {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'number') {
    return value.toFixed(2)
  }
  return String(value)
}

const getValueClass = (varData: any) => {
  if (varData.value === null || varData.value === undefined) return 'no-data'
  const num = Number(varData.value)
  if (isNaN(num)) return 'normal'
  if (varData.min !== undefined && varData.max !== undefined) {
    if (num >= varData.max) return 'danger'
    if (num <= varData.min) return 'warning'
  }
  return 'normal'
}

const refreshDBStatus = async () => {
  try {
    const configRes = await getConfig()
    const collectorRes = await getCollectorStatus()
    
    dbStatus.value = {
      connected: configRes.data.db_enabled || false,
      dbType: configRes.data.db_type || '',
      collectorRunning: collectorRes.data.running || false,
      variablesCount: collectorRes.data.variables_count || 0
    }
    
    systemForm.value.collectorEnabled = collectorRes.data.running || false
    systemForm.value.collectorInterval = collectorRes.data.interval_ms || 2000
  } catch (error) {
    console.error('获取数据库状态失败:', error)
    ElMessage.error('获取数据库状态失败')
  }
}

const fetchVariables = async () => {
  try {
    const varsRes = await getMonitorVariables()
    if (varsRes.data.success) {
      // 将 (name, type) 元组格式转换为对象数组
      variables.value = varsRes.data.variables.map((v: [string, string]) => ({
        name: v[0],
        type: v[1]
      }))
      if (variables.value.length > 0 && !selectedHistoryVariable.value) {
        selectedHistoryVariable.value = variables.value[0].name
      }
      await fetchRealtimeData()
    }
  } catch (error) {
    console.error('获取变量列表失败:', error)
  }
}

const fetchRealtimeData = async () => {
  try {
    if (variables.value.length > 0) {
      const varNames = variables.value.map((v: any) => v.name)
      const dataRes = await getRealtimeData(varNames)
      if (dataRes.data.success) {
        const dataMap = dataRes.data.data as Record<string, any>
        realtimeData.value = variables.value.map((v: any) => ({
          ...v,
          value: dataMap[v.name]?.value ?? null
        }))
        filterVariables()
      }
    }
  } catch (error) {
    console.error('获取实时数据失败:', error)
  }
}

const filterVariables = () => {
  if (!searchKeyword.value) {
    filteredVariables.value = realtimeData.value
  } else {
    const keyword = searchKeyword.value.toLowerCase()
    filteredVariables.value = realtimeData.value.filter((item: any) => 
      item.name.toLowerCase().includes(keyword) ||
      (item.comment && item.comment.toLowerCase().includes(keyword))
    )
  }
}

const loadHistoryData = async () => {
  if (!selectedHistoryVariable.value) {
    ElMessage.warning('请选择变量')
    return
  }
  
  try {
    const res = await getHistoryData(
      selectedHistoryVariable.value,
      historyHours.value,
      historyAggregation.value
    )
    if (res.data.success) {
      historyData.value = res.data.data
      nextTick(() => {
        renderChart()
      })
    }
  } catch (error) {
    console.error('获取历史数据失败:', error)
    ElMessage.error('获取历史数据失败')
  }
}

const renderChart = () => {
  if (!chartRef.value) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value)
  
  const option = {
    title: {
      text: `${selectedHistoryVariable.value} 历史数据`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: historyData.value.map((item: any) => item.timestamp || '')
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '数值',
        type: 'line',
        smooth: true,
        data: historyData.value.map((item: any) => item.value || 0)
      }
    ]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart?.resize()
  })
}

const toggleCollector = async (value: boolean) => {
  try {
    if (value) {
      const res = await startCollector()
      if (res.data.success) {
        ElMessage.success('数据采集已启动')
      } else {
        ElMessage.error(res.data.message || '启动失败')
        systemForm.value.collectorEnabled = false
      }
    } else {
      const res = await stopCollector()
      if (res.data.success) {
        ElMessage.success('数据采集已停止')
      } else {
        ElMessage.error(res.data.message || '停止失败')
        systemForm.value.collectorEnabled = true
      }
    }
    await refreshDBStatus()
  } catch (error) {
    console.error('切换采集器状态失败:', error)
    ElMessage.error('操作失败')
  }
}

const saveSystemSettings = async () => {
  ElMessage.success('设置已保存')
  await refreshDBStatus()
}

const clearDatabase = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空数据库吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const res = await clearAllDataAPI()
    if (res.data.success) {
      ElMessage.success('数据库已清空')
      await fetchRealtimeData()
    } else {
      ElMessage.error('清空数据库失败')
    }
  } catch (error) {
    // 取消操作
  }
}

const clearVariableData = async (variable: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要清空变量 ${variable.name} 的数据吗？此操作不可恢复。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const res = await clearVariableDataAPI(variable.name)
    if (res.data.success) {
      ElMessage.success(`变量 ${variable.name} 的数据已清空`)
      await fetchRealtimeData()
    } else {
      ElMessage.error(`清空变量 ${variable.name} 的数据失败`)
    }
  } catch (error) {
    // 取消操作
  }
}

const showVariableDetails = (variable: any) => {
  currentVariable.value = variable
  detailDialogVisible.value = true
}

const showVariableHistory = (variable: any) => {
  currentVariable.value = variable
  dialogHistoryHours.value = 1
  historyDialogVisible.value = true
  nextTick(() => {
    loadDialogHistoryData()
  })
}

const loadDialogHistoryData = async () => {
  if (!currentVariable.value) return
  
  try {
    const res = await getHistoryData(
      currentVariable.value.name,
      dialogHistoryHours.value,
      'mean'
    )
    if (res.data.success) {
      const dialogHistoryData = res.data.data
      nextTick(() => {
        renderHistoryChart(dialogHistoryData)
      })
    }
  } catch (error) {
    console.error('获取历史数据失败:', error)
  }
}

const renderHistoryChart = (data: any[]) => {
  if (!historyChartRef.value) return
  
  if (historyChart) {
    historyChart.dispose()
  }
  
  historyChart = echarts.init(historyChartRef.value)
  
  const option = {
    title: {
      text: '历史数据趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map((item: any) => item.timestamp || '')
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: currentVariable.value?.name,
        type: 'line',
        smooth: true,
        data: data.map((item: any) => item.value || 0)
      }
    ]
  }
  
  historyChart.setOption(option)
  
  window.addEventListener('resize', () => {
    historyChart?.resize()
  })
}

watch(searchKeyword, () => {
  filterVariables()
})

watch(selectedHistoryVariable, () => {
  if (selectedHistoryVariable.value) {
    loadHistoryData()
  }
})

onMounted(async () => {
  await refreshDBStatus()
  await fetchVariables()
  
  setInterval(async () => {
    await fetchRealtimeData()
  }, 3000)
})
</script>

<style scoped>
.database-view {
  padding: 20px 0;
}

.db-header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.db-status-info {
  margin-top: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
}

.status-label {
  font-size: 14px;
  color: #606266;
  min-width: 80px;
}

.status-value {
  font-size: 14px;
  font-weight: 500;
}

.status-success {
  color: #67c23a;
}

.status-error {
  color: #f56c6c;
}

.status-warning {
  color: #e6a23c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-management {
  padding: 0 20px;
}

.history-data {
  padding: 0 20px;
}

.system-management {
  padding: 0 20px;
}

.history-controls {
  display: flex;
  gap: 10px;
  margin: 16px 0;
  align-items: center;
}

.chart-container {
  margin-top: 20px;
}

.chart {
  width: 100%;
  height: 400px;
}

.empty-history {
  text-align: center;
  padding: 60px 0;
  color: #909399;
}

.empty-history p {
  margin-top: 16px;
}

.variable-detail {
  padding: 20px 0;
}

.history-dialog-content {
  height: 400px;
  display: flex;
  flex-direction: column;
}

.history-dialog-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  align-items: center;
}

.history-chart {
  flex: 1;
  width: 100%;
  min-height: 300px;
}

:deep(.el-table .no-data) {
  color: #909399;
}

:deep(.el-table .normal) {
  color: #409eff;
}

:deep(.el-table .warning) {
  color: #e6a23c;
}

:deep(.el-table .danger) {
  color: #f56c6c;
}

:deep(.el-table .no-data) {
  color: #c0c4cc;
}
</style>