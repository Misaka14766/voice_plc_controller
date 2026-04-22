<template>
  <div class="plc-monitor">
    <!-- PLC设备信息卡片 -->
    <el-card class="device-info-card">
      <template #header>
        <div class="card-header">
          <h2>PLC设备信息</h2>
          <el-button type="primary" @click="refreshDeviceInfo" :loading="loadingDevice">
            <el-icon><Refresh /></el-icon> 刷新信息
          </el-button>
        </div>
      </template>
      
      <div class="device-info-content">
        <div class="device-image">
          <img 
            :src="deviceImageSrc" 
            alt="Beckhoff C6030" 
            class="device-img"
            @error="handleImageError">
        </div>
        
        <div class="device-details">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <span class="info-label">设备型号:</span>
                <span class="info-value">
                  <a v-if="deviceInfo.modelLink" :href="deviceInfo.modelLink" target="_blank" class="info-link">{{ deviceInfo.model }}</a>
                  <span v-else>{{ deviceInfo.model }}</span>
                </span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="info-label">系统:</span>
                <span class="info-value">
                  <a v-if="deviceInfo.systemLink" :href="deviceInfo.systemLink" target="_blank" class="info-link">{{ deviceInfo.system }}</a>
                  <span v-else>{{ deviceInfo.system }}</span>
                </span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="info-label">状态:</span>
                <span class="info-value" :class="plcConnected ? 'status-connected' : 'status-disconnected'">
                  {{ plcConnected ? '已连接' : '未连接' }}
                </span>
              </div>
            </el-col>
          </el-row>
          
          <el-row :gutter="20" class="mt-2">
            <el-col :span="8">
              <div class="info-item">
                <span class="info-label">IP地址:</span>
                <span class="info-value">{{ deviceInfo.ipAddress }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="info-label">变量数量:</span>
                <span class="info-value">{{ variables.length }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="info-label">实时更新:</span>
                <el-switch v-model="realtimeUpdate" @change="toggleRealtimeUpdate" />
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <!-- 变量监控卡片 -->
    <el-card class="variables-card">
      <template #header>
        <div class="card-header">
          <h2>变量监控</h2>
          <div class="header-actions">
            <el-button type="primary" @click="refreshVariables" :loading="loading">
              <el-icon><Refresh /></el-icon> 刷新变量
            </el-button>
            <el-button type="success" @click="toggleMainModuleOnly" :loading="loading">
              {{ mainModuleOnly ? '显示全部' : '仅主模块' }}
            </el-button>
            <el-button :type="isMonitoring ? 'danger' : 'success'" @click="toggleMonitoring">
              {{ isMonitoring ? '停止监控' : '启动监控' }}
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="!plcConnected" class="plc-disconnected">
        <el-alert
          title="PLC未连接"
          type="warning"
          :closable="false"
          show-icon
        />
        <p>请检查PLC连接状态后重试</p>
      </div>

      <div v-else class="variables-container">
        <!-- 搜索和过滤 -->
        <div class="search-filter-section">
          <el-input
            v-model="searchQuery"
            placeholder="搜索变量"
            class="search-input"
            clearable
            @input="filteredVariables"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select v-model="typeFilter" placeholder="按类型过滤" class="type-filter">
            <el-option label="全部" value="" />
            <el-option label="BOOL" value="BOOL" />
            <el-option label="INT" value="INT" />
            <el-option label="REAL" value="REAL" />
            <el-option label="STRING" value="STRING" />
          </el-select>
        </div>

        <!-- 变量表格 -->
        <el-table
          :data="filteredVariables"
          style="width: 100%"
          stripe
          :loading="loading"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="name" label="变量名" min-width="200">
            <template #default="scope">
              <span class="variable-name" :class="{ 'hidden-variable': !scope.row.visible }">{{ scope.row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="100">
            <template #default="scope">
              <span :class="{ 'hidden-variable': !scope.row.visible }">{{ scope.row.type }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="当前值" min-width="150">
            <template #default="scope">
              <div v-if="editingVariable === scope.row.name && !scope.row.locked && scope.row.visible" class="edit-value">
                <el-input
                  v-model="editValue"
                  @keyup.enter="saveValue(scope.row)"
                  @blur="cancelEdit"
                  ref="editInput"
                />
                <el-button type="primary" size="small" @click="saveValue(scope.row)">
                  保存
                </el-button>
                <el-button size="small" @click="cancelEdit">
                  取消
                </el-button>
              </div>
              <div v-else class="value-cell">
                <span @click="startEdit(scope.row)" class="value-text" :class="{ 'locked': scope.row.locked, 'hidden-variable': !scope.row.visible }">
                  {{ scope.row.visible ? scope.row.value : '（隐藏）' }}
                  <el-icon class="edit-icon" v-if="!scope.row.locked && scope.row.visible"><Edit /></el-icon>
                  <el-icon class="lock-icon" v-else-if="scope.row.locked"><Lock /></el-icon>
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="注释" min-width="200" />
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="scope">
              <div class="variable-actions">
                <el-button 
                  :type="scope.row.visible ? 'default' : 'info' " 
                  size="small" 
                  @click="toggleVariableVisibility(scope.row)"
                  :class="{'white-button': scope.row.visible, 'gray-button': !scope.row.visible}"
                >
                  <el-icon v-if="scope.row.visible"><View /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                  {{ scope.row.visible ? ' 隐藏' : ' 显示' }}
                </el-button>
                <el-button 
                  :type="scope.row.locked ? 'info' : 'default' " 
                  size="small" 
                  @click="toggleVariableLock(scope.row)"
                  :class="{'white-button': !scope.row.locked, 'gray-button': scope.row.locked}"
                >
                  <el-icon v-if="scope.row.locked"><Lock /></el-icon>
                  <el-icon v-else><Unlock /></el-icon>
                  {{ scope.row.locked ? ' 解锁' : ' 锁定' }}
                </el-button>
                <el-tooltip :content="scope.row.monitored ? '点击移除监控' : '点击加入监控'" placement="top">
                  <el-button 
                    :type="scope.row.monitored ? 'success' : 'info'" 
                    size="small" 
                    @click="toggleVariableMonitoring(scope.row)"
                  >
                    {{ scope.row.monitored ? '已监控' : '未监控' }}
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 批量操作 -->
        <div class="batch-operations" v-if="selectedVariables.length > 0">
          <el-button type="primary" size="small" @click="batchReadValues">
            <el-icon><Reading /></el-icon> 批量读取
          </el-button>
          <el-button type="success" size="small" @click="batchEditValues">
            <el-icon><Edit /></el-icon> 批量编辑
          </el-button>
          <el-button type="warning" size="small" @click="batchToggleLock">
            <el-icon><Lock /></el-icon> 批量锁定/解锁
          </el-button>
          <el-button type="info" size="small" @click="batchToggleVisibility">
            <el-icon><View /></el-icon> 批量显示/隐藏
          </el-button>
        </div>

        <div v-if="filteredVariables.length === 0" class="empty-state">
          <el-empty description="暂无变量数据" />
        </div>
      </div>
    </el-card>

    <!-- 批量编辑对话框 -->
    <el-dialog v-model="batchEditDialogVisible" title="批量编辑变量" width="500px">
      <el-form :model="batchEditForm">
        <el-form-item label="新值">
          <el-input v-model="batchEditForm.value" placeholder="请输入新值" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchEditDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBatchEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Refresh, Edit, Search, Link, View, Hide, Lock, Unlock, Reading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listPLCVariables, readPLC, writePLC, getPLCDeviceInfo, readPLCList, writePLCList, getMonitorVariables, updateMonitorVariables } from '../api'

// 加载状态
const loading = ref(false)
const loadingDevice = ref(false)
const plcConnected = ref(false)

// 设备信息
const deviceInfo = ref({
  model: 'Beckhoff C6030',
  system: 'TwinCAT 3',
  ipAddress: '192.168.1.100',
  status: '未知',
  modelLink: '',
  systemLink: '',
  imageUrl: ''
})

// 设备图片路径
const deviceImageSrc = ref('')

// 处理图片加载失败
const handleImageError = () => {
  // 当图片加载失败时，使用默认图片
  deviceImageSrc.value = 'https://multimedia.beckhoff.com/media/c6030_main1__web.jpg.webp'
}

// 变量数据
const variables = ref<any[]>([])
const selectedVariables = ref<any[]>([])
const editingVariable = ref('')
const editValue = ref('')
const editInput = ref()
const searchQuery = ref('')
const typeFilter = ref('')
const realtimeUpdate = ref(true)
const mainModuleOnly = ref(false)
const isMonitoring = ref(true)
const monitorVariables = ref<{name: string, type: string}[]>([])

// 批量编辑
const batchEditDialogVisible = ref(false)
const batchEditForm = ref({ value: '' })

// 定时器
const intervalId = ref<number | null>(null)

// 过滤变量
const filteredVariables = computed(() => {
  let result = variables.value
  
  // 按搜索词过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(v => 
      v.name.toLowerCase().includes(query) || 
      v.type.toLowerCase().includes(query) ||
      (v.comment && v.comment.toLowerCase().includes(query))
    )
  }
  
  // 按类型过滤
  if (typeFilter.value) {
    result = result.filter(v => v.type === typeFilter.value)
  }
  
  // 按主模块过滤
  if (mainModuleOnly.value) {
    result = result.filter(v => v.name.startsWith('MAIN.'))
  }
  
  // 按显示状态排序（显示的在前，隐藏的在后）
  result.sort((a, b) => {
    if (a.visible && !b.visible) return -1
    if (!a.visible && b.visible) return 1
    return 0
  })
  
  return result
})

// 刷新设备信息
const refreshDeviceInfo = async () => {
  loadingDevice.value = true
  try {
    const response = await getPLCDeviceInfo()
    if (response.data.success) {
      deviceInfo.value = {
        model: response.data.model || 'Beckhoff C6030',
        system: response.data.system || 'TwinCAT 3',
        ipAddress: response.data.ipAddress || '192.168.1.100',
        status: response.data.status || '正常',
        modelLink: response.data.modelLink || '',
        systemLink: response.data.systemLink || '',
        imageUrl: response.data.imageUrl || ''
      }
      // 更新设备图片路径
      deviceImageSrc.value = deviceInfo.value.imageUrl
    }
  } catch (error) {
    console.error('获取设备信息失败:', error)
  } finally {
    loadingDevice.value = false
  }
}

// 获取监控变量列表
const fetchMonitorVariables = async () => {
  try {
    const response = await getMonitorVariables()
    if (response.data.success) {
      monitorVariables.value = response.data.variables.map((v: [string, string]) => ({
        name: v[0],
        type: v[1]
      }))
    }
  } catch (error) {
    console.error('获取监控变量列表失败:', error)
  }
}

// 刷新变量列表
const refreshVariables = async () => {
  loading.value = true
  try {
    // 先获取监控变量列表
    await fetchMonitorVariables()
    
    const response = await listPLCVariables()
    if (response.data.success) {
      plcConnected.value = true
      // 为每个变量添加额外属性
      const varsWithProperties = await Promise.all(
        response.data.variables.map(async (varItem: any) => {
          try {
            // 尝试读取变量值
            const readResponse = await readPLC(varItem.name, varItem.type)
            return {
              ...varItem,
              value: readResponse.data.success ? readResponse.data.value : '读取失败',
              visible: true,
              locked: false,
              monitored: monitorVariables.value.some(mv => mv.name === varItem.name),
              lastUpdated: new Date().toISOString()
            }
          } catch (error) {
            return {
              ...varItem,
              value: '读取失败',
              visible: true,
              locked: false,
              monitored: monitorVariables.value.some(mv => mv.name === varItem.name),
              lastUpdated: new Date().toISOString()
            }
          }
        })
      )
      variables.value = varsWithProperties
    } else {
      plcConnected.value = false
      variables.value = []
    }
  } catch (error) {
    plcConnected.value = false
    variables.value = []
  } finally {
    loading.value = false
  }
}

// 开始编辑变量值
const startEdit = (row: any) => {
  if (row.locked) {
    ElMessage.warning('该变量已锁定，无法编辑')
    return
  }
  if (!row.visible) {
    ElMessage.warning('该变量已隐藏，无法编辑')
    return
  }
  editingVariable.value = row.name
  editValue.value = row.value.toString()
  nextTick(() => {
    if (editInput.value) {
      (editInput.value as any).focus()
    }
  })
}

// 保存变量值
const saveValue = async (row: any) => {
  try {
    const response = await writePLC(row.name, editValue.value, row.type)
    if (response.data.success) {
      // 更新本地变量值
      const index = variables.value.findIndex(v => v.name === row.name)
      if (index !== -1) {
        variables.value[index].value = editValue.value
        variables.value[index].lastUpdated = new Date().toISOString()
      }
      editingVariable.value = ''
      editValue.value = ''
      ElMessage.success('保存成功')
    } else {
      ElMessage.error(`保存失败: ${response.data.error}`)
    }
  } catch (error) {
    ElMessage.error('保存失败，请重试')
  }
}

// 取消编辑
const cancelEdit = () => {
  editingVariable.value = ''
  editValue.value = ''
}

// 切换变量可见性
const toggleVariableVisibility = (row: any) => {
  row.visible = !row.visible
}

// 切换变量锁定状态
const toggleVariableLock = (row: any) => {
  row.locked = !row.locked
  ElMessage.success(row.locked ? '变量已锁定' : '变量已解锁')
}

// 切换主模块过滤
const toggleMainModuleOnly = () => {
  mainModuleOnly.value = !mainModuleOnly.value
  ElMessage.success(mainModuleOnly.value ? '仅显示主模块变量' : '显示全部变量')
}

// 切换监控状态
const toggleMonitoring = () => {
  isMonitoring.value = !isMonitoring.value
  ElMessage.success(isMonitoring.value ? '监控已启动' : '监控已停止')
  if (isMonitoring.value && realtimeUpdate.value) {
    startRealtimeUpdate()
  } else {
    stopRealtimeUpdate()
  }
}

// 切换变量监控状态
const toggleVariableMonitoring = async (row: any) => {
  try {
    row.monitored = !row.monitored
    
    // 更新监控变量列表
    if (row.monitored) {
      if (!monitorVariables.value.some(v => v.name === row.name)) {
        monitorVariables.value.push({ name: row.name, type: row.type })
      }
    } else {
      monitorVariables.value = monitorVariables.value.filter(v => v.name !== row.name)
    }
    
    // 调用后端API更新监控变量
    const response = await updateMonitorVariables(monitorVariables.value)
    if (response.data.success) {
      ElMessage.success(row.monitored ? '变量已加入监控' : '变量已移出监控')
    } else {
      // 回滚操作
      row.monitored = !row.monitored
      if (row.monitored) {
        monitorVariables.value.push({ name: row.name, type: row.type })
      } else {
        monitorVariables.value = monitorVariables.value.filter(v => v.name !== row.name)
      }
      ElMessage.error('更新监控状态失败')
    }
  } catch (error) {
    // 回滚操作
    row.monitored = !row.monitored
    if (row.monitored) {
      monitorVariables.value.push({ name: row.name, type: row.type })
    } else {
      monitorVariables.value = monitorVariables.value.filter(v => v.name !== row.name)
    }
    ElMessage.error('更新监控状态失败')
  }
}

// 处理选择变化
const handleSelectionChange = (val: any[]) => {
  selectedVariables.value = val
}

// 批量读取值
const batchReadValues = async () => {
  if (selectedVariables.value.length === 0) {
    ElMessage.warning('请选择要读取的变量')
    return
  }
  
  loading.value = true
  try {
    const variableNames = selectedVariables.value.map(v => v.name)
    const response = await readPLCList(variableNames)
    if (response.data.success) {
      const values = response.data.values
      // 更新本地变量值
      Object.entries(values).forEach(([varName, value]) => {
        const index = variables.value.findIndex(item => item.name === varName)
        if (index !== -1) {
          variables.value[index].value = value
          variables.value[index].lastUpdated = new Date().toISOString()
        }
      })
      ElMessage.success(`成功读取 ${Object.keys(values).length} 个变量`)
    }
  } catch (error) {
    ElMessage.error('批量读取失败，请重试')
  } finally {
    loading.value = false
  }
}

// 批量编辑
const batchEditValues = () => {
  if (selectedVariables.value.length === 0) {
    ElMessage.warning('请选择要编辑的变量')
    return
  }
  batchEditDialogVisible.value = true
}

// 保存批量编辑
const saveBatchEdit = async () => {
  if (!batchEditForm.value.value) {
    ElMessage.warning('请输入新值')
    return
  }
  
  loading.value = true
  try {
    // 构建批量写入对象
    const variablesToWrite: Record<string, any> = {}
    selectedVariables.value.forEach(v => {
      if (!v.locked && v.visible) {
        variablesToWrite[v.name] = batchEditForm.value.value
      }
    })
    
    if (Object.keys(variablesToWrite).length === 0) {
      ElMessage.warning('没有可编辑的变量')
      loading.value = false
      return
    }
    
    const response = await writePLCList(variablesToWrite)
    if (response.data.success) {
      const results = response.data.results
      let successCount = 0
      
      // 更新本地变量值
      Object.entries(results).forEach(([varName, result]) => {
        if (result === 'no error') {
          const index = variables.value.findIndex(v => v.name === varName)
          if (index !== -1) {
            variables.value[index].value = batchEditForm.value.value
            variables.value[index].lastUpdated = new Date().toISOString()
            successCount++
          }
        }
      })
      
      ElMessage.success(`成功修改 ${successCount} 个变量`)
      batchEditDialogVisible.value = false
      batchEditForm.value.value = ''
    } else {
      ElMessage.error('批量修改失败')
    }
  } catch (error) {
    ElMessage.error('批量修改失败，请重试')
  } finally {
    loading.value = false
  }
}

// 批量锁定/解锁
const batchToggleLock = () => {
  if (selectedVariables.value.length === 0) {
    ElMessage.warning('请选择要操作的变量')
    return
  }
  
  const lockedCount = selectedVariables.value.filter(v => v.locked).length
  const newLockState = lockedCount < selectedVariables.value.length
  
  selectedVariables.value.forEach(v => {
    v.locked = newLockState
  })
  
  ElMessage.success(newLockState ? '变量已锁定' : '变量已解锁')
}

// 批量显示/隐藏
const batchToggleVisibility = () => {
  if (selectedVariables.value.length === 0) {
    ElMessage.warning('请选择要操作的变量')
    return
  }
  
  const visibleCount = selectedVariables.value.filter(v => v.visible).length
  const newVisibleState = visibleCount < selectedVariables.value.length
  
  selectedVariables.value.forEach(v => {
    v.visible = newVisibleState
  })
  
  ElMessage.success(newVisibleState ? '变量已显示' : '变量已隐藏')
}

// 切换实时更新
const toggleRealtimeUpdate = () => {
  if (realtimeUpdate.value) {
    startRealtimeUpdate()
  } else {
    stopRealtimeUpdate()
  }
}

// 开始实时更新
const startRealtimeUpdate = () => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
  intervalId.value = setInterval(() => {
    // 只在监控状态下更新
    if (!isMonitoring.value) return
    
    // 只更新可见且未锁定的变量
    const visibleVariables = variables.value.filter(v => v.visible && !v.locked)
    if (visibleVariables.length > 0) {
      // 批量读取可见变量
      const variableNames = visibleVariables.map(v => v.name)
      if (variableNames.length > 0) {
        readPLCList(variableNames).then(response => {
          if (response.data.success) {
            const values = response.data.values
            Object.entries(values).forEach(([varName, value]) => {
              const index = variables.value.findIndex(item => item.name === varName)
              if (index !== -1) {
                variables.value[index].value = value
                variables.value[index].lastUpdated = new Date().toISOString()
              }
            })
          }
        }).catch(error => {
          // 静默失败，避免频繁弹窗
        })
      }
    }
  }, 1000) // 1秒更新一次
}

// 停止实时更新
const stopRealtimeUpdate = () => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
    intervalId.value = null
  }
}

// 组件挂载时初始化
onMounted(() => {
  refreshDeviceInfo()
  refreshVariables()
  if (realtimeUpdate.value) {
    startRealtimeUpdate()
  }
})

// 组件卸载时清理
onUnmounted(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})
</script>

<style scoped>
.plc-monitor {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.device-info-card {
  margin-bottom: 20px;
}

.variables-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.device-info-content {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
}

.device-image {
  flex: 0 0 300px;
}

.device-img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.device-details {
  flex: 1;
  min-width: 400px;
}

.info-item {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.info-label {
  width: 100px;
  font-weight: 500;
  color: #606266;
}

.info-value {
  color: #303133;
  font-weight: 600;
}

.info-link {
  color: #409EFF;
  text-decoration: none;
  transition: color 0.3s;
}

.info-link:hover {
  color: #66B1FF;
  text-decoration: underline;
}

.status-connected {
  color: #67C23A;
}

.status-disconnected {
  color: #F56C6C;
}

.device-links {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.plc-disconnected {
  text-align: center;
  padding: 40px 0;
}

.variables-container {
  margin-top: 20px;
}

.search-filter-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-input {
  width: 300px;
}

.type-filter {
  width: 150px;
}

.variable-name {
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.hidden-variable {
  color: #C0C4CC;
  font-style: italic;
}

.value-cell {
  display: flex;
  align-items: center;
}

.value-text {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
  transition: all 0.3s;
}

.value-text:hover:not(.locked):not(.hidden-variable) {
  color: #409EFF;
}

.value-text.locked {
  color: #909399;
  cursor: not-allowed;
}

.value-text.hidden-variable {
  color: #C0C4CC;
  cursor: not-allowed;
}

.edit-icon,
.lock-icon {
  margin-left: 8px;
  opacity: 0.6;
  font-size: 14px;
  transition: opacity 0.3s;
}

.value-text:hover .edit-icon {
  opacity: 1;
}

.edit-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.edit-value .el-input {
  flex: 1;
  max-width: 200px;
}

.variable-actions {
  display: flex;
  gap: 5px;
}

.white-button {
  background-color: #ffffff !important;
  border-color: #dcdfe6 !important;
  color: #303133 !important;
}

.gray-button {
  background-color: #f5f7fa !important;
  border-color: #c0c4cc !important;
  color: #909399 !important;
}

.batch-operations {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.empty-state {
  margin: 40px 0;
}

.mt-2 {
  margin-top: 10px;
}

@media (max-width: 768px) {
  .device-info-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .device-image {
    flex: 0 0 auto;
  }
  
  .device-details {
    min-width: auto;
  }
  
  .search-filter-section {
    flex-direction: column;
  }
  
  .search-input,
  .type-filter {
    width: 100%;
  }
}
</style>
