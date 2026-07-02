<template>
  <div class="stores-page">
    <div class="page-header">
      <h2>店铺管理</h2>
      <el-button type="primary" @click="showDialog = true">添加店铺</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8" v-for="store in appStore.stores" :key="store.id">
        <el-card shadow="hover" class="store-card">
          <div class="store-header">
            <h3>{{ store.name }}</h3>
            <el-tag size="small">{{ platformLabel(store.platform) }}</el-tag>
          </div>
          <div class="store-info">
            <p>创建时间：{{ formatDate(store.created_at) }}</p>
            <p>自动回复：<el-tag :type="store.auto_reply_enabled ? 'success' : 'info'" size="small">{{ store.auto_reply_enabled ? '已开启' : '已关闭' }}</el-tag></p>
          </div>
          <div class="store-actions">
            <el-button type="primary" size="small" @click="appStore.setCurrentStore(store.id)">进入管理</el-button>
            <el-button size="small" @click="editStore(store)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="deleteStore(store.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!appStore.stores.length" description="还没有店铺，点击上方按钮添加" />

    <!-- 添加/编辑店铺对话框 -->
    <el-dialog v-model="showDialog" :title="editingStore ? '编辑店铺' : '添加店铺'" width="450px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="店铺名称" prop="name">
          <el-input v-model="form.name" placeholder="输入店铺名称" />
        </el-form-item>
        <el-form-item label="平台" prop="platform">
          <el-select v-model="form.platform" placeholder="选择平台" style="width: 100%">
            <el-option label="拼多多" value="pinduoduo" />
            <el-option label="淘宝" value="taobao" />
            <el-option label="京东" value="jd" />
          </el-select>
        </el-form-item>
        <el-form-item label="自动回复">
          <el-switch v-model="form.auto_reply_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import storesApi from '@/api/stores'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const showDialog = ref(false)
const editingStore = ref(null)
const saving = ref(false)
const formRef = ref(null)
const form = reactive({ name: '', platform: 'pinduoduo', auto_reply_enabled: true })
const rules = {
  name: [{ required: true, message: '请输入店铺名称', trigger: 'blur' }],
  platform: [{ required: true, message: '请选择平台', trigger: 'change' }]
}

function platformLabel(p) {
  return { pinduoduo: '拼多多', taobao: '淘宝', jd: '京东' }[p] || p
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString()
}

function editStore(store) {
  editingStore.value = store
  form.name = store.name
  form.platform = store.platform
  form.auto_reply_enabled = store.auto_reply_enabled
  showDialog.value = true
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (editingStore.value) {
      await storesApi.update(editingStore.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await storesApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    editingStore.value = null
    form.name = ''
    form.platform = 'pinduoduo'
    form.auto_reply_enabled = true
    await appStore.fetchStores()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function deleteStore(id) {
  try {
    await storesApi.remove(id)
    ElMessage.success('已删除')
    await appStore.fetchStores()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.store-card { margin-bottom: 20px; }
.store-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.store-header h3 { margin: 0; }
.store-info p { color: #666; font-size: 14px; margin: 6px 0; }
.store-actions { margin-top: 16px; display: flex; gap: 8px; }
</style>
