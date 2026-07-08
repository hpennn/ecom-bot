<template>
  <div class="page-container">
    <div class="page-header">
      <h2>🧑‍💼 转人工配置</h2>
      <el-button type="primary" @click="showDialog = true">添加规则</el-button>
    </div>

    <el-alert title="当用户消息包含以下关键词时，自动转接人工客服" type="info" :closable="false" style="margin-bottom: 16px" />

    <el-table :data="items" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="触发关键词" width="350">
        <template #default="{ row }">
          <el-tag v-for="kw in row.keywords" :key="kw" type="danger" size="small" style="margin: 2px">{{ kw }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reply_message" label="提示话术" show-overflow-tooltip />
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
          <el-select v-model="form.keywords" multiple filterable allow-create default-first-option placeholder="如：转人工、投诉、退款" style="width: 100%" />
        </el-form-item>
        <el-form-item label="提示话术">
          <el-input v-model="form.reply_message" placeholder="正在为您转接人工客服，请稍候..." />
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

const items = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({ keywords: [], reply_message: '正在为您转接人工客服，请稍候...', is_active: true })
const storeId = 1

const loadData = async () => {
  const res = await request.get('/api/knowledge/transfer', { params: { store_id: storeId } })
  items.value = res.data.items
}

const saveItem = async () => {
  if (editingId.value) {
    await request.put(`/api/knowledge/transfer/${editingId.value}`, form.value)
  } else {
    await request.post('/api/knowledge/transfer', { ...form.value, store_id: storeId })
  }
  showDialog.value = false
  editingId.value = null
  form.value = { keywords: [], reply_message: '正在为您转接人工客服，请稍候...', is_active: true }
  loadData()
}

const editItem = (row) => {
  editingId.value = row.id
  form.value = { keywords: row.keywords, reply_message: row.reply_message, is_active: row.is_active }
  showDialog.value = true
}

const deleteItem = async (id) => {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await request.delete(`/api/knowledge/transfer/${id}`)
  ElMessage.success('已删除')
  loadData()
}

const toggleActive = async (row) => {
  await request.put(`/api/knowledge/transfer/${row.id}`, { is_active: row.is_active })
}

onMounted(loadData)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
