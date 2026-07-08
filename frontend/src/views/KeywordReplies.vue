<template>
  <div class="page-container">
    <div class="page-header">
      <h2>🔑 关键词回复管理</h2>
      <el-button type="primary" @click="showDialog = true">添加规则</el-button>
    </div>

    <el-table :data="replies" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="关键词" width="300">
        <template #default="{ row }">
          <el-tag v-for="kw in row.keywords" :key="kw" size="small" style="margin: 2px">{{ kw }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reply" label="回复内容" show-overflow-tooltip />
      <el-table-column prop="match_type" label="匹配方式" width="100">
        <template #default="{ row }">
          <el-tag :type="row.match_type === 'exact' ? 'success' : row.match_type === 'regex' ? 'warning' : 'info'" size="small">
            {{ { contains: '包含', exact: '精确', regex: '正则' }[row.match_type] || '包含' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="toggleActive(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="editItem(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteItem(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="editingId ? '编辑规则' : '添加规则'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="关键词">
          <el-select v-model="form.keywords" multiple filterable allow-create default-first-option placeholder="输入关键词后回车添加" style="width: 100%" />
        </el-form-item>
        <el-form-item label="回复内容">
          <el-input v-model="form.reply" type="textarea" :rows="3" placeholder="匹配到关键词后的回复内容" />
        </el-form-item>
        <el-form-item label="匹配方式">
          <el-radio-group v-model="form.match_type">
            <el-radio value="contains">包含匹配</el-radio>
            <el-radio value="exact">精确匹配</el-radio>
            <el-radio value="regex">正则匹配</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const replies = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({ keywords: [], reply: '', match_type: 'contains', priority: 0, is_active: true })

const storeId = 1 // TODO: from store context

const loadData = async () => {
  const res = await request.get('/api/knowledge/keywords', { params: { store_id: storeId } })
  replies.value = res.data.items
}

const saveItem = async () => {
  if (editingId.value) {
    await request.put(`/api/knowledge/keywords/${editingId.value}`, form.value)
    ElMessage.success('更新成功')
  } else {
    await request.post('/api/knowledge/keywords', { ...form.value, store_id: storeId })
    ElMessage.success('创建成功')
  }
  showDialog.value = false
  editingId.value = null
  form.value = { keywords: [], reply: '', match_type: 'contains', priority: 0, is_active: true }
  loadData()
}

const editItem = (row) => {
  editingId.value = row.id
  form.value = { keywords: row.keywords, reply: row.reply, match_type: row.match_type, priority: row.priority, is_active: row.is_active }
  showDialog.value = true
}

const deleteItem = async (id) => {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await request.delete(`/api/knowledge/keywords/${id}`)
  ElMessage.success('已删除')
  loadData()
}

const toggleActive = async (row) => {
  await request.put(`/api/knowledge/keywords/${row.id}`, { is_active: row.is_active })
}

onMounted(loadData)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
