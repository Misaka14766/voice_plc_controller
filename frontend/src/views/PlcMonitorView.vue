<template>
  <div class="plc-monitor">
    <el-card class="card-container">
      <template #header>
        <div class="card-header">
          <h2>PLC监控</h2>
          <el-button type="primary" @click="refreshVariables" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新变量
          </el-button>
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
        <el-input
          v-model="searchQuery"
          placeholder="搜索变量"
          class="search-input"
          prefix-icon="Search"
        />

        <el-table
          :data="filteredVariables"
          style="width: 100%"
          stripe
          :loading="loading"
        >
          <el-table-column prop="name" label="变量名" min-width="200" />
          <el-table-column prop="type" label="类型" width="100" />
          <el-table-column prop="value" label="当前值" min-width="150">
            <template #default="scope">
              <div v-if="editingVariable === scope.row.name" class="edit-value">
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
              <div v-else @click="startEdit(scope.row)" class="value-cell">
                {{ scope.row.value }}
                <el-icon class="edit-icon"><Edit /></el-icon>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="注释" min-width="200" />
        </el-table>

        <div v-if="filteredVariables.length === 0" class="empty-state">
          <el-empty description="暂无变量数据" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Refresh, Edit, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listPLCVariables, readPLC, writePLC } from '../api'

const loading = ref(false)
const plcConnected = ref(false)
const variables = ref<any[]>([])
const searchQuery = ref('')
const editingVariable = ref('')
const editValue = ref('')
const editInput = ref()
const intervalId = ref<number | null>(null)

// 过滤变量
const filteredVariables = computed(() => {
  if (!searchQuery.value) {
    return variables.value
  }
  const query = searchQuery.value.toLowerCase()
  return variables.value.filter(v => 
    v.name.toLowerCase().includes(query) || 
    v.type.toLowerCase().includes(query) ||
    (v.comment && v.comment.toLowerCase().includes(query))
  )
})

// 刷新变量列表
const refreshVariables = async () => {
  loading.value = true
  try {
    const response = await listPLCVariables()
    if (response.data.success) {
      plcConnected.value = true
      // 为每个变量添加value属性
      const varsWithValue = await Promise.all(
        response.data.variables.map(async (v: any) => {
          try {
            // 尝试读取变量值
            const readResponse = await readPLC(v.name, v.type)
            return {
              ...v,
              value: readResponse.data.success ? readResponse.data.value : '读取失败'
            }
          } catch (error) {
            return {
              ...v,
              value: '读取失败'
            }
          }
        })
      )
      variables.value = varsWithValue
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
      }
      editingVariable.value = ''
      editValue.value = ''
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

// 组件挂载时刷新变量
onMounted(() => {
  refreshVariables()
  // 每5秒自动刷新
  intervalId.value = setInterval(refreshVariables, 5000)
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})
</script>

<style scoped>
.plc-monitor {
  padding: 20px;
}

.card-container {
  max-width: 1200px;
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

.plc-disconnected {
  text-align: center;
  padding: 40px 0;
}

.variables-container {
  margin-top: 20px;
}

.search-input {
  margin-bottom: 20px;
  width: 300px;
}

.value-cell {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
}

.edit-icon {
  margin-left: 8px;
  opacity: 0.6;
  font-size: 14px;
}

.value-cell:hover .edit-icon {
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

.empty-state {
  margin: 40px 0;
}
</style>
