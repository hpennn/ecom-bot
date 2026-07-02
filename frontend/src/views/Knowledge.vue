<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h2>知识库管理</h2>
      <div class="header-actions">
        <el-button type="success" @click="showTestDialog = true">测试回复</el-button>
        <el-button type="primary" @click="showDialog = true">添加条目</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card style="margin-bottom: 16px">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-select v-model="filterCategory" placeholder="按分类筛选" clearable style="width: 100%" @change="loadData">
            <el-option label="FAQ" value="faq" />
            <el-option label="商品信息" value="product" />
            <el-option label="售后政策" value="policy" />
            <el-option label="物流信息" value="logistics" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="searchText" placeholder="搜索问题关键词" clearable @clear="loadData" @keyup.enter="loadData" />
        </el-col>
      </el-row>
    </el-card>

    <!-- 知识条目表格 -->
    <el-card>
      <el-table :data="items" style="width: 100%" v-loading="loading">
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="categoryColor(row.category)">{{ categoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question" label="问题/关键词" min-width="200" show-overflow-tooltip />
        <el-table-column prop="answer" label="回复内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="80" align="center" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editItem(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="deleteItem(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!items.length && !loading" description="暂无知识条目" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingItem ? '编辑知识条目' : '添加知识条目'" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="FAQ" value="faq" />
            <el-option label="商品信息" value="product" />
            <el-option label="售后政策" value="policy" />
            <el-option label="物流信息" value="logistics" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题" prop="question">
          <el-input v-model="form.question" placeholder="输入问题或关键词" />
        </el-form-item>
        <el-form-item label="回复" prop="answer">
          <el-input v-model="form.answer" type="textarea" :rows="4" placeholder="输入回复内容" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-slider v-model="form.priority" :min="1" :max="10" show-stops />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 测试回复对话框 -->
    <el-dialog v-model="showTestDialog" title="测试自动回复" width="500px">
      <el-input v-model="testQuestion" placeholder="输入测试问题" style="margin-bottom: 16px" />
      <el-button type="primary" :loading="testing" @click="handleTest" :disabled="!testQuestion">测试</el-button>
      <div v-if="testResult" class="test-result">
        <h4>回复结果：</h4>
        <div class="result-content">{{ testResult }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import knowledgeApi from '@/api/knowledge'
import api from '@/utils/request'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const loading = ref(false)
const items = ref([])
const filterCategory = ref('')
const searchText = ref('')
const showDialog = ref(false)
const showTestDialog = ref(false)
const editingItem = ref(null)
const saving = ref(false)
const testing = ref(false)
const testQuestion = ref('')
const testResult = ref('')
const formRef = ref(null)
const form = reactive({ category: 'faq', question: '', answer: '', priority: 5 })
const rules = {
  category: [{ required: true, message: '请选择分类' }],
  question: [{ required: true, message: '请输入问题' }],
  answer: [{ required: true, message: '请输入回复内容' }]
}

function categoryLabel(c) {
  return { faq: 'FAQ', product: '商品', policy: '售后', logistics: '物流', custom: '自定义' }[c] || c
}
function categoryColor(c) {
  return { faq: '', product: 'success', policy: 'warning', logistics: 'info', custom: 'danger' }[c] || ''
}

async function loadData() {
  if (!appStore.currentStoreId) return
  loading.value = true
  try {
    let data = await knowledgeApi.getList(appStore.currentStoreId)
    if (filterCategory.value) data = data.filter(i => i.category === filterCategory.value)
    if (searchText.value) {
      const kw = searchText.value.toLowerCase()
      data = data.filter(i => i.question.toLowerCase().includes(kw) || i.answer.toLowerCase().includes(kw))
    }
    items.value = data
  } catch (e) {
    items.value = []
  } finally {
    loading.value = false
  }
}

function editItem(item) {
  editingItem.value = item
  form.category = item.category
  form.question = item.question
  form.answer = item.answer
  form.priority = item.priority
  showDialog.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (editingItem.value) {
      await knowledgeApi.update(editingItem.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await knowledgeApi.create(appStore.currentStoreId, form)
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    editingItem.value = null
    Object.assign(form, { category: 'faq', question: '', answer: '', priority: 5 })
    await loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function deleteItem(id) {
  try {
    await knowledgeApi.remove(id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function handleTest() {
  if (!appStore.currentStoreId || !testQuestion.value) return
  testing.value = true
  testResult.value = ''
  try {
    const data = await api.post(`/stores/${appStore.currentStoreId}/reply`, { message: testQuestion.value })
    testResult.value = data.reply || data.message || '无回复'
  } catch (e) {
    testResult.value = '测试失败：' + (e.response?.data?.detail || e.message)
  } finally {
    testing.value = false
  }
}

watch(() => appStore.currentStoreId, loadData)
onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-actions { display: flex; gap: 8px; }
.test-result { margin-top: 16px; }
.test-result h4 { margin-bottom: 8px; color: #666; }
.result-content { padding: 12px; background: #f5f7fa; border-radius: 8px; line-height: 1.6; }
</style>
