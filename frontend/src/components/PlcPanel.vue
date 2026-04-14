<template>
  <el-collapse v-model="activeNames" class="plc-panel">
    <el-collapse-item title="PLC 变量监控" name="plc">
      <div class="panel-header">
        <el-button type="primary" size="small" @click="refreshList" :loading="loading">
          刷新列表
        </el-button>
      </div>
      <el-table :data="variables" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="变量名" min-width="180" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="comment" label="注释" min-width="150" />
        <el-table-column label="当前值" width="120">
          <template #default="scope">
            <span v-if="scope.row.currentValue !== undefined">{{ scope.row.currentValue }}</span>
            <span v-else style="color: #909399">未读取</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="readVariable(scope.row)">读取</el-button>
            <el-button size="small" @click="showWriteDialog(scope.row)">写入</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-collapse-item>
  </el-collapse>

  <!-- 写入对话框 -->
  <el-dialog v-model="writeDialogVisible" title="写入变量" width="400px">
    <el-form :model="writeForm" label-width="80px">
      <el-form-item label="变量名">
        <el-input v-model="writeForm.variable" disabled />
      </el-form-item>
      <el-form-item label="类型">
        <el-input v-model="writeForm.dataType" disabled />
      </el-form-item>
      <el-form-item label="写入值">
        <el-input v-model="writeForm.value" placeholder="请输入新值" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="writeDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitWrite">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { listPLCVariables, readPLC, writePLC, type PLCVariable } from '../api'

const activeNames = ref(['plc'])
const variables = ref<(PLCVariable & { currentValue?: any })[]>([])
const loading = ref(false)
const writeDialogVisible = ref(false)
const writeForm = reactive({
  variable: '',
  dataType: 'INT',
  value: ''
})

const refreshList = async () => {
  loading.value = true
  try {
    const res = await listPLCVariables()
    if (res.data.success) {
      variables.value = res.data.variables.map(v => ({ ...v, currentValue: undefined }))
      ElMessage.success(`已加载 ${variables.value.length} 个变量`)
    } else {
      ElMessage.error(res.data.error || '获取变量列表失败')
    }
  } catch (e) {
    ElMessage.error('请求失败')
  } finally {
    loading.value = false
  }
}

const readVariable = async (row: PLCVariable) => {
  try {
    const res = await readPLC(row.name, row.type)
    if (res.data.success) {
      const target = variables.value.find(v => v.name === row.name)
      if (target) target.currentValue = res.data.value
      ElMessage.success(`${row.name} = ${res.data.value}`)
    } else {
      ElMessage.error(res.data.error || '读取失败')
    }
  } catch (e) {
    ElMessage.error('请求失败')
  }
}

const showWriteDialog = (row: PLCVariable) => {
  writeForm.variable = row.name
  writeForm.dataType = row.type
  writeForm.value = ''
  writeDialogVisible.value = true
}

const submitWrite = async () => {
  if (!writeForm.value.trim()) {
    ElMessage.warning('请输入值')
    return
  }
  try {
    const res = await writePLC(writeForm.variable, writeForm.value, writeForm.dataType)
    if (res.data.success) {
      ElMessage.success(`成功写入 ${writeForm.variable}`)
      writeDialogVisible.value = false
      // 自动刷新该变量值
      const target = variables.value.find(v => v.name === writeForm.variable)
      if (target) await readVariable(target)
    } else {
      ElMessage.error(res.data.error || '写入失败')
    }
  } catch (e) {
    ElMessage.error('请求失败')
  }
}
</script>

<style scoped>
.panel-header {
  margin-bottom: 16px;
}
</style>
