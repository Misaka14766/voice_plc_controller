<template>
  <div class="data-view">
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="stat in statsCards" :key="stat.title">
        <el-card class="stat-card" :class="stat.type">
          <div class="stat-content">
            <el-icon class="stat-icon" :size="32">
              <component :is="stat.icon" />
            </el-icon>
            <div class="stat-info">
              <span class="stat-label">{{ stat.title }}</span>
              <span class="stat-value">{{ stat.value }}</span>
              <span class="stat-unit">{{ stat.unit }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="controls-row">
      <el-col :span="24">
        <el-card class="control-card">
          <div class="controls">
            <div class="control-item">
              <label>选择变量</label>
              <el-select v-model="selectedVariable" placeholder="请选择变量" @change="onVariableChange">
                <el-option
                  v-for="v in variables"
                  :key="v"
                  :label="v"
                  :value="v"
                />
              </el-select>
            </div>
            <div class="control-item">
              <label>时间范围</label>
              <el-select v-model="timeRange" placeholder="请选择时间范围" @change="onTimeRangeChange">
                <el-option label="最近30分钟" value="30m" />
                <el-option label="最近1小时" value="1h" />
                <el-option label="最近6小时" value="6h" />
                <el-option label="最近12小时" value="12h" />
                <el-option label="最近24小时" value="24h" />
                <el-option label="最近7天" value="7d" />
              </el-select>
            </div>
            <div class="control-item">
              <label>聚合方式</label>
              <el-select v-model="aggregation" placeholder="请选择聚合方式" @change="onAggregationChange">
                <el-option label="平均值" value="mean" />
                <el-option label="最大值" value="max" />
                <el-option label="最小值" value="min" />
                <el-option label="求和" value="sum" />
              </el-select>
            </div>
            <div class="control-item">
              <label>刷新间隔</label>
              <el-select v-model="refreshInterval" placeholder="请选择刷新间隔">
                <el-option label="关闭自动刷新" value="0" />
                <el-option label="5秒" value="5000" />
                <el-option label="10秒" value="10000" />
                <el-option label="30秒" value="30000" />
                <el-option label="1分钟" value="60000" />
              </el-select>
            </div>
            <el-button type="primary" @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span class="chart-title">
                <el-icon><DataLine /></el-icon>
                {{ selectedVariable || '请选择变量' }} - 历史趋势
              </span>
              <div class="chart-actions">
                <el-button size="small" @click="exportData">
                  <el-icon><Download /></el-icon> 导出数据
                </el-button>
              </div>
            </div>
          </template>
          <div ref="chartRef" class="chart-container"></div>
          <div v-if="!selectedVariable" class="empty-chart">
            <el-empty description="请从上方选择要查看的变量" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="table-row">
      <el-col :span="24">
        <el-card class="table-card">
          <template #header>
            <div class="table-header">
              <span class="table-title">
                <el-icon><Document /></el-icon>
                数据详情
              </span>
              <span class="data-count">共 {{ tableData.length }} 条记录</span>
            </div>
          </template>
          <el-table
            :data="tableData"
            stripe
            border
            :loading="loading"
            height="300"
            :default-sort="{ prop: 'timestamp', order: 'descending' }"
          >
            <el-table-column prop="timestamp" label="时间" width="180" sortable />
            <el-table-column prop="variable_name" label="变量名" width="200" />
            <el-table-column prop="value" label="数值" width="120">
              <template #default="scope">
                <span class="value-tag">{{ formatValue(scope.row.value) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="data_type" label="类型" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="info-row">
      <el-col :xs="24" :sm="12">
        <el-card class="info-card">
          <template #header>
            <span class="info-title">
              <el-icon><InfoFilled /></el-icon>
              数据采集状态
            </span>
          </template>
          <div class="info-content">
            <div class="info-item">
              <span class="info-label">采集器状态</span>
              <el-tag :type="collectorStatus.running ? 'success' : 'info'">
                {{ collectorStatus.running ? '运行中' : '已停止' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">采集间隔</span>
              <span class="info-value">{{ collectorStatus.interval_ms }}ms</span>
            </div>
            <div class="info-item">
              <span class="info-label">监控变量数</span>
              <span class="info-value">{{ collectorStatus.variables_count || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">缓冲区大小</span>
              <span class="info-value">{{ collectorStatus.buffer_size || 0 }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="info-card">
          <template #header>
            <span class="info-title">
              <el-icon><DataAnalysis /></el-icon>
              数据库状态
            </span>
          </template>
          <div class="info-content">
            <div class="info-item">
              <span class="info-label">数据库类型</span>
              <el-tag>{{ dbType.toUpperCase() }}</el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">连接状态</span>
              <el-tag :type="dbConnected ? 'success' : 'danger'">
                {{ dbConnected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
            <div class="info-item" v-if="dbStatus.total_records !== undefined">
              <span class="info-label">总记录数</span>
              <span class="info-value">{{ formatNumber(dbStatus.total_records) }}</span>
            </div>
            <div class="info-item" v-if="dbStatus.variable_count !== undefined">
              <span class="info-label">变量数量</span>
              <span class="info-value">{{ dbStatus.variable_count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Refresh, DataLine, Download, Document, InfoFilled, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getConfig, getChartData, getCollectorStatus, listPLCVariables } from '../api'

const loading = ref(false)
const chartRef = ref<HTMLElement>()
const variables = ref<string[]>([])
const selectedVariable = ref('')
const timeRange = ref('1h')
const aggregation = ref('mean')
const refreshInterval = ref('5000')
const tableData = ref<any[]>([])
const chartData = ref<any[]>([])

const collectorStatus = reactive({
  running: false,
  interval_ms: 0,
  variables_count: 0,
  buffer_size: 0
})

const dbType = ref('sqlite')
const dbConnected = ref(false)
const dbStatus = reactive<any>({})

let chartInstance: echarts.ECharts | null = null
let refreshTimer: number | null = null

const statsCards = computed(() => {
  if (!chartData.value.length) {
    return [
      { title: '当前值', value: '--', unit: '', icon: 'TrendCharts', type: 'primary' },
      { title: '平均值', value: '--', unit: '', icon: 'DataLine', type: 'success' },
      { title: '最大值', value: '--', unit: '', icon: 'Top', type: 'warning' },
      { title: '最小值', value: '--', unit: '', icon: 'Bottom', type: 'danger' }
    ]
  }

  const values = chartData.value.map(d => d.value)
  const current = values[values.length - 1]
  const avg = values.reduce((a, b) => a + b, 0) / values.length
  const max = Math.max(...values)
  const min = Math.min(...values)

  return [
    { title: '当前值', value: formatNumber(current), unit: '', icon: 'TrendCharts', type: 'primary' },
    { title: '平均值', value: formatNumber(avg), unit: '', icon: 'DataLine', type: 'success' },
    { title: '最大值', value: formatNumber(max), unit: '', icon: 'Top', type: 'warning' },
    { title: '最小值', value: formatNumber(min), unit: '', icon: 'Bottom', type: 'danger' }
  ]
})

const formatNumber = (num: number): string => {
  if (num === null || num === undefined) return '--'
  return Number(num).toFixed(2)
}

const formatValue = (val: any): string => {
  if (val === null || val === undefined) return '--'
  return typeof val === 'number' ? Number(val).toFixed(4) : String(val)
}

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.axisValue}<br/>${data.marker} ${data.seriesName}: <b>${formatNumber(data.value)}</b>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [],
      axisLabel: {
        formatter: (value: string) => {
          const date = new Date(value)
          return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
        }
      }
    },
    yAxis: {
      type: 'value',
      scale: true
    },
    series: [
      {
        name: selectedVariable.value || '数值',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        sampling: 'lttb',
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        },
        data: []
      }
    ]
  }

  chartInstance.setOption(option)
}

const updateChart = () => {
  if (!chartInstance) {
    initChart()
  }

  const times = chartData.value.map(d => d.timestamp)
  const values = chartData.value.map(d => d.value)

  chartInstance?.setOption({
    xAxis: { data: times },
    series: [{
      name: selectedVariable.value,
      data: values
    }]
  })
}

const loadChartData = async () => {
  if (!selectedVariable.value) return

  loading.value = true
  try {
    const response = await getChartData(selectedVariable.value, timeRange.value, aggregation.value)
    if (response.data.success) {
      chartData.value = response.data.data || []
      tableData.value = [...chartData.value].reverse()
      updateChart()
    } else {
      ElMessage.error('获取图表数据失败')
    }
  } catch (error) {
    console.error('获取图表数据失败:', error)
    ElMessage.error('获取图表数据失败，请检查数据库连接')
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  await loadChartData()
  await loadCollectorStatus()
}

const onVariableChange = () => {
  loadChartData()
}

const onTimeRangeChange = () => {
  loadChartData()
}

const onAggregationChange = () => {
  loadChartData()
}

const loadCollectorStatus = async () => {
  try {
    const response = await getCollectorStatus()
    if (response.data.success) {
      Object.assign(collectorStatus, response.data)
    }
  } catch (error) {
    console.error('获取采集器状态失败:', error)
  }
}

const loadConfig = async () => {
  try {
    const response = await getConfig()
    if (response.data.db_enabled) {
      dbType.value = response.data.db_type || 'sqlite'
      dbConnected.value = true
    }
  } catch (error) {
    console.error('获取配置失败:', error)
  }
}

const loadVariables = async () => {
  try {
    const response = await listPLCVariables()
    if (response.data.success && response.data.variables) {
      variables.value = response.data.variables.map((v: any) => v.name)
    }
  } catch (error) {
    console.error('获取变量列表失败:', error)
  }
}

const exportData = () => {
  if (!tableData.value.length) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const headers = ['时间', '变量名', '数值', '类型']
  const rows = tableData.value.map(item => [
    item.timestamp,
    item.variable_name,
    item.value,
    item.data_type
  ])

  const csvContent = [headers, ...rows]
    .map(row => row.join(','))
    .join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedVariable.value}_${timeRange.value}_${Date.now()}.csv`
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success('数据导出成功')
}

const startAutoRefresh = () => {
  stopAutoRefresh()

  const interval = parseInt(refreshInterval.value)
  if (interval > 0) {
    refreshTimer = window.setInterval(() => {
      loadChartData()
    }, interval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

watch(refreshInterval, () => {
  startAutoRefresh()
})

watch(selectedVariable, (newVal) => {
  if (newVal && !variables.value.includes(newVal)) {
    variables.value.push(newVal)
  }
})

onMounted(async () => {
  await nextTick()
  initChart()

  await loadConfig()
  await loadCollectorStatus()
  await loadVariables()

  const lastVariable = localStorage.getItem('lastSelectedVariable')
  const lastTimeRange = localStorage.getItem('lastTimeRange')

  if (lastVariable) selectedVariable.value = lastVariable
  if (lastTimeRange) timeRange.value = lastTimeRange

  if (selectedVariable.value) {
    await loadChartData()
  }

  startAutoRefresh()

  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})

onUnmounted(() => {
  stopAutoRefresh()
  chartInstance?.dispose()
  window.removeEventListener('resize', () => {
    chartInstance?.resize()
  })

  if (selectedVariable.value) {
    localStorage.setItem('lastSelectedVariable', selectedVariable.value)
  }
  if (timeRange.value) {
    localStorage.setItem('lastTimeRange', timeRange.value)
  }
})
</script>

<style scoped>
.data-view {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
  border-radius: 8px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card.primary {
  border-left: 4px solid #409EFF;
}

.stat-card.success {
  border-left: 4px solid #67C23A;
}

.stat-card.warning {
  border-left: 4px solid #E6A23C;
}

.stat-card.danger {
  border-left: 4px solid #F56C6C;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  padding: 12px;
  border-radius: 8px;
  background: #f5f7fa;
}

.stat-card.primary .stat-icon {
  color: #409EFF;
  background: #ecf5ff;
}

.stat-card.success .stat-icon {
  color: #67C23A;
  background: #f0f9eb;
}

.stat-card.warning .stat-icon {
  color: #E6A23C;
  background: #fdf6ec;
}

.stat-card.danger .stat-icon {
  color: #F56C6C;
  background: #fef0f0;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-unit {
  font-size: 12px;
  color: #c0c4cc;
}

.controls-row {
  margin-bottom: 20px;
}

.control-card {
  border-radius: 8px;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-item label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.control-item .el-select {
  width: 160px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 8px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.chart-actions {
  display: flex;
  gap: 8px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.empty-chart {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-row {
  margin-bottom: 20px;
}

.table-card {
  border-radius: 8px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.data-count {
  font-size: 14px;
  color: #909399;
}

.value-tag {
  font-family: 'Monaco', 'Menlo', monospace;
  color: #409EFF;
}

.info-row {
  margin-bottom: 20px;
}

.info-card {
  border-radius: 8px;
  height: 100%;
}

.info-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.info-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 14px;
  color: #909399;
}

.info-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

@media (max-width: 768px) {
  .controls {
    flex-direction: column;
    align-items: stretch;
  }

  .control-item .el-select {
    width: 100%;
  }

  .chart-container {
    height: 300px;
  }

  .info-content {
    grid-template-columns: 1fr;
  }
}
</style>
