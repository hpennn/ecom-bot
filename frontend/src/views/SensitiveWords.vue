<template>
  <div class="page-container">
    <div class="page-header">
      <h2>🛡️ 敏感词管理</h2>
      <div>
        <el-button @click="showBatchDialog = true">批量添加</el-button>
        <el-button type="primary" @click="showDialog = true">添加敏感词</el-button>
      </div>
    </div>

    <el-alert title="用户消息中包含敏感词时，系统将自动过滤并拒绝回复" type="warning" :closable="false" style="margin-bottom: 16px" />

    <el-table :data="items" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="word" label="敏感词" width="200" />
      <el-table-column prop="replacement" label="替换为" width="150" />
      <el-table-column label="范围" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_global ? 'danger' : 'info'" size="small">{{ row.is_global ? '全局' : '店铺' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="deleteItem(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" title="添加敏感词" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="敏感词">
          <el-input v-model="form.word" placeholder="输入敏感词" />
        </el-form-item>
        <el-form-item label="替换为">
          <el-input v-model="form.replacement" placeholder="***" />
        </el-form-item>
        <el-form-item label="全局生效">
          <el-switch v-model="form.is_global" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showBatchDialog" title="批量添加敏感词" width="500px">
      <el-input v-model="batchText" type="textarea" :rows="6" placeholder="每行一个敏感词，可用 | 分隔替换词，如：脏话|***" />
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="batchSave">批量添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const items = ref([])
const showDialog = ref(false)
const showBatchDialog = ref(false)
const batchText = ref('')
const form = ref({ word: '', replacement: '***', is_global: false })
const storeId = 1

const loadData = async () => {
  const res = await request.get('/api/knowledge/sensitive', { params: { store_id: storeId } })
  items.value = res.data.items
}

const saveItem = async () => {
  await request.post('/api/knowledge/sensitive', { ...form.value, store_id: storeId })
  ElMessage.success('添加成功')
  showDialog.value = false
  form.value = { word: '', replacement: '***', is_global: false }
  loadData()
}

const batchSave = async () => {
  const lines = batchText.value.split('\n').filter(l => l.trim())
  for (const line of lines) {
    const [word, replacement] = line.split('|').map(s => s.trim())
    if (word) {
      await request.post('/api/knowledge/sensitive', { word, replacement: replacement || '***', store_id: storeId, is_global: false })
    }
  }
  ElMessage.success(`已添加 ${lines.length} 个敏感词`)
  showBatchDialog.value = false
  batchText.value = ''
  loadData()
}

const deleteItem = async (id) => {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await request.delete(`/api/knowledge/sensitive/${id}`)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
