<template>
  <div class="knowledge-view">
    <el-card class="header-card">
      <template #header>
        <div class="header-content">
          <span class="header-title">知识库管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加词条
          </el-button>
        </div>
      </template>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409EFF"><Document /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ entries.length }}</span>
              <span class="stat-label">词条总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67C23A"><Collection /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ totalTags }}</span>
              <span class="stat-label">标签数量</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索知识库内容..."
              clearable
              @input="filterEntries"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="entries-card">
      <template #header>
        <span>知识库词条</span>
      </template>
      <el-table :data="filteredEntries" style="width: 100%">
        <el-table-column prop="question" label="问题" min-width="200">
          <template #default="scope">
            <span class="question-text">{{ scope.row.question }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="answer" label="答案" min-width="300">
          <template #default="scope">
            <span class="answer-text">{{ scope.row.answer }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" width="200">
          <template #default="scope">
            <el-tag v-for="tag in scope.row.tags" :key="tag" size="small" class="tag-item">
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="editEntry(scope.row, scope.$index)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="deleteEntry(scope.$index)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="preview-card">
      <template #header>
        <span>LLM 知识召回测试</span>
      </template>
      <div class="test-area">
        <el-input
          v-model="testQuery"
          placeholder="输入测试问题，如：水位低怎么办？"
          type="textarea"
          :rows="2"
        />
        <el-button type="primary" @click="testKnowledgeRecall" :loading="testing">
          测试召回
        </el-button>
        <div v-if="testResult" class="test-result">
          <h4>召回结果：</h4>
          <pre>{{ testResult }}</pre>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="问题">
          <el-input v-model="form.question" placeholder="请输入问题" />
        </el-form-item>
        <el-form-item label="答案">
          <el-input
            v-model="form.answer"
            type="textarea"
            :rows="4"
            placeholder="请输入答案"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in allTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEntry">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Document, Collection } from '@element-plus/icons-vue'
import axios from 'axios'

interface KnowledgeEntry {
  question: string
  answer: string
  tags: string[]
}

const entries = ref<KnowledgeEntry[]>([])
const searchKeyword = ref('')
const filteredEntries = ref<KnowledgeEntry[]>([])
const testQuery = ref('')
const testResult = ref('')
const testing = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('添加词条')
const editingIndex = ref(-1)

const form = ref<KnowledgeEntry>({
  question: '',
  answer: '',
  tags: []
})

const allTags = computed(() => {
  const tags = new Set<string>()
  entries.value.forEach(e => e.tags?.forEach(t => tags.add(t)))
  return Array.from(tags).sort()
})

const totalTags = computed(() => allTags.value.length)

const filterEntries = () => {
  if (!searchKeyword.value) {
    filteredEntries.value = [...entries.value]
  } else {
    const keyword = searchKeyword.value.toLowerCase()
    filteredEntries.value = entries.value.filter(e =>
      e.question.toLowerCase().includes(keyword) ||
      e.answer.toLowerCase().includes(keyword) ||
      e.tags?.some(t => t.toLowerCase().includes(keyword))
    )
  }
}

const loadKnowledgeBase = async () => {
  try {
    const res = await axios.get('/api/knowledge')
    if (res.data.success) {
      entries.value = res.data.entries || []
      filterEntries()
    }
  } catch (error) {
    console.error('加载知识库失败:', error)
    entries.value = []
  }
}

const showAddDialog = () => {
  dialogTitle.value = '添加词条'
  editingIndex.value = -1
  form.value = { question: '', answer: '', tags: [] }
  dialogVisible.value = true
}

const editEntry = (entry: KnowledgeEntry, index: number) => {
  dialogTitle.value = '编辑词条'
  editingIndex.value = index
  form.value = { ...entry, tags: [...entry.tags] }
  dialogVisible.value = true
}

const saveEntry = async () => {
  if (!form.value.question || !form.value.answer) {
    ElMessage.warning('请填写问题和答案')
    return
  }

  try {
    if (editingIndex.value >= 0) {
      entries.value[editingIndex.value] = { ...form.value }
      ElMessage.success('词条已更新')
    } else {
      entries.value.push({ ...form.value })
      ElMessage.success('词条已添加')
    }
    filterEntries()
    dialogVisible.value = false

    await axios.post('/api/knowledge', { entries: entries.value })
  } catch (error) {
    console.error('保存知识库失败:', error)
    ElMessage.error('保存失败')
  }
}

const deleteEntry = async (index: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条词条吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    entries.value.splice(index, 1)
    filterEntries()
    ElMessage.success('词条已删除')

    await axios.post('/api/knowledge', { entries: entries.value })
  } catch {
    // 用户取消
  }
}

const testKnowledgeRecall = async () => {
  if (!testQuery.value.trim()) {
    ElMessage.warning('请输入测试问题')
    return
  }

  testing.value = true
  testResult.value = ''

  try {
    const res = await axios.get('/api/knowledge/test', {
      params: { query: testQuery.value }
    })
    testResult.value = res.data.result || '未找到匹配结果'
  } catch (error) {
    console.error('测试召回失败:', error)
    testResult.value = '测试失败，请检查后端服务'
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadKnowledgeBase()
})
</script>

<style scoped>
.knowledge-view {
  padding: 20px 0;
}

.header-card {
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

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.entries-card {
  margin-bottom: 20px;
}

.question-text {
  font-weight: 500;
  color: #303133;
}

.answer-text {
  color: #606266;
  line-height: 1.5;
}

.tag-item {
  margin-right: 4px;
  margin-bottom: 4px;
}

.preview-card {
  margin-bottom: 20px;
}

.test-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.test-result {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
}

.test-result h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.test-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: inherit;
  color: #303133;
}
</style>