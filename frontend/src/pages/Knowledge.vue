<template>
  <div class="knowledge-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>知识库管理</h2>
        <p v-if="currentStore">{{ currentStore.name }} - 知识库</p>
        <el-tag v-else type="warning">请先选择店铺</el-tag>
      </div>
      <div class="header-right button-group">
        <el-upload
          :action="`/api/stores/${currentStoreId}/knowledge/batch`"
          :headers="{ Authorization: `Bearer ${token}` }"
          :show-file-list="false"
          :on-success="handleImportSuccess"
          :on-error="handleImportError"
          accept=".csv,.xlsx,.xls"
        >
          <el-button :disabled="!currentStoreId">
            <el-icon><Upload /></el-icon>
            批量导入
          </el-button>
        </el-upload>
        <el-button type="primary" :disabled="!currentStoreId" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加知识
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar page-card">
      <el-radio-group v-model="filterCategory" @change="handleFilterChange">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="FAQ">FAQ</el-radio-button>
        <el-radio-button label="商品信息">商品信息</el-radio-button>
        <el-radio-button label="售后政策">售后政策</el-radio-button>
        <el-radio-button label="物流信息">物流信息</el-radio-button>
        <el-radio-button label="自定义">自定义</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 知识列表 -->
    <div class="page-card" v-loading="loading">
      <el-table :data="knowledgeList" stripe style="width: 100%">
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)">
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question" label="问题/关键词" min-width="200" show-overflow-tooltip />
        <el-table-column prop="answer" label="回答" min-width="300" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.priority || 5 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" text size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && knowledgeList.length === 0" description="暂无知识条目" />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingItem ? '编辑知识' : '添加知识'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
            <el-option label="FAQ" value="FAQ" />
            <el-option label="商品信息" value="商品信息" />
            <el-option label="售后政策" value="售后政策" />
            <el-option label="物流信息" value="物流信息" />
            <el-option label="自定义" value="自定义" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="问题" prop="question">
          <el-input 
            v-model="form.question" 
            placeholder="请输入问题或关键词，多个关键词用逗号分隔"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="回答" prop="answer">
          <el-input
            v-model="form.answer"
            type="textarea"
            :rows="4"
            placeholder="请输入AI回复内容"
          />
        </el-form-item>
        
        <el-form-item label="优先级" prop="priority">
          <el-slider v-model="form.priority" :min="1" :max="10" :marks="priorityMarks" show-stops />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试回复对话框 -->
    <el-dialog v-model="testDialogVisible" title="测试回复" width="600px">
      <div class="test-area">
        <el-input
          v-model="testQuestion"
          placeholder="输入测试问题"
          type="textarea"
          :rows="2"
        />
        <el-button type="primary" :loading="testing" @click="handleTest" style="margin-top: 12px;">
          发送测试
        </el-button>
        
        <div v-if="testResult" class="test-result">
          <h4>AI 回复：</h4>
          <div class="result-content">{{ testResult }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useStoreStore } from '@/stores/store'
import { useKnowledgeStore } from '@/stores/knowledge'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const storeStore = useStoreStore()
const knowledgeStore = useKnowledgeStore()
const authStore = useAuthStore()

// 状态
const loading = computed(() => knowledgeStore.loading)
const knowledgeList = computed(() => knowledgeStore.knowledgeList)
const currentStore = computed(() => storeStore.currentStore)
const currentStoreId = computed(() => storeStore.currentStoreId)
const token = computed(() => authStore.token)

// 筛选
const filterCategory = ref('')

// 添加/编辑对话框
const dialogVisible = ref(false)
const editingItem = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  category: 'FAQ',
  question: '',
  answer: '',
  priority: 5
})

const rules = {
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  question: [{ required: true, message: '请输入问题', trigger: 'blur' }],
  answer: [{ required: true, message: '请输入回答', trigger: 'blur' }]
}

const priorityMarks = {
  1: '低',
  5: '中',
  10: '高'
}

// 测试对话框
const testDialogVisible = ref(false)
const testQuestion = ref('')
const testResult = computed(() => knowledgeStore.testResult)
const testing = computed(() => knowledgeStore.testing)

// 获取分类标签类型
const getCategoryType = (category) => {
  const types = {
    'FAQ': 'primary',
    '商品信息': 'success',
    '售后政策': 'warning',
    '物流信息': 'info',
    '自定义': 'danger'
  }
  return types[category] || 'info'
}

// 加载知识列表
const loadKnowledge = async () => {
  if (!currentStoreId.value) return
  await knowledgeStore.fetchKnowledgeList(currentStoreId.value, {
    category: filterCategory.value
  })
}

// 处理筛选变化
const handleFilterChange = () => {
  loadKnowledge()
}

// 显示添加对话框
const showAddDialog = () => {
  editingItem.value = null
  form.category = 'FAQ'
  form.question = ''
  form.answer = ''
  form.priority = 5
  dialogVisible.value = true
}

// 编辑知识
const handleEdit = (row) => {
  editingItem.value = row
  form.category = row.category
  form.question = row.question
  form.answer = row.answer
  form.priority = row.priority || 5
  dialogVisible.value = true
}

// 删除知识
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这条知识吗？`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await knowledgeStore.deleteKnowledgeAction(row.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (editingItem.value) {
      await knowledgeStore.updateKnowledgeAction(editingItem.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await knowledgeStore.addKnowledgeAction(currentStoreId.value, form)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadKnowledge()
  } catch (error) {
    // 错误已由 axios 拦截器处理
  } finally {
    submitting.value = false
  }
}

// 测试回复
const handleTest = async () => {
  if (!testQuestion.value.trim()) {
    ElMessage.warning('请输入测试问题')
    return
  }
  await knowledgeStore.testReplyAction(currentStoreId.value, testQuestion.value)
  if (testResult.value) {
    ElMessage.success('测试完成')
  }
}

// 导入成功
const handleImportSuccess = () => {
  ElMessage.success('导入成功')
  loadKnowledge()
}

// 导入失败
const handleImportError = () => {
  ElMessage.error('导入失败，请检查文件格式')
}

// 监听店铺变化
watch(currentStoreId, (newVal) => {
  if (newVal) {
    loadKnowledge()
  }
})

onMounted(() => {
  if (currentStoreId.value) {
    loadKnowledge()
  }
})
</script>

<style scoped>
.knowledge-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.header-left p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.filter-bar {
  margin-bottom: 20px;
}

.test-area {
  padding: 10px 0;
}

.test-result {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.test-result h4 {
  margin: 0 0 12px 0;
  color: #409eff;
}

.result-content {
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
