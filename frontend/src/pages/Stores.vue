<template>
  <div class="stores-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>店铺管理</h2>
        <p>管理您的电商店铺</p>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建店铺
      </el-button>
    </div>

    <!-- 店铺列表 -->
    <div class="stores-grid" v-loading="loading">
      <div v-if="stores.length === 0 && !loading" class="empty-state">
        <el-icon class="empty-icon"><Shop /></el-icon>
        <p>暂无店铺</p>
        <el-button type="primary" @click="showCreateDialog = true">
          创建第一个店铺
        </el-button>
      </div>

      <el-row :gutter="20" v-else>
        <el-col 
          v-for="store in stores" 
          :key="store.id" 
          :xs="24" :sm="12" :md="8" :lg="6"
        >
          <div class="store-card page-card" @click="goToStore(store)">
            <div class="store-header">
              <div class="store-platform">
                <el-tag :type="getPlatformType(store.platform)">
                  {{ store.platform }}
                </el-tag>
              </div>
              <el-dropdown trigger="click" @click.stop>
                <el-button text size="small">
                  <el-icon><More /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click.stop="handleEdit(store)">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item @click.stop="handleDelete(store)" divided>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            
            <h3 class="store-name">{{ store.name }}</h3>
            
            <div class="store-info">
              <div class="info-item">
                <span class="label">状态</span>
                <el-tag :type="store.status === 'active' ? 'success' : 'info'" size="small">
                  {{ store.status === 'active' ? '运行中' : '已停用' }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">创建时间</span>
                <span>{{ formatDate(store.createdAt) }}</span>
              </div>
            </div>
            
            <div class="store-stats">
              <div class="stat-item">
                <span class="value">{{ store.conversationCount || 0 }}</span>
                <span class="label">对话</span>
              </div>
              <div class="stat-item">
                <span class="value">{{ store.knowledgeCount || 0 }}</span>
                <span class="label">知识</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 创建/编辑店铺对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingStore ? '编辑店铺' : '创建店铺'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="店铺名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入店铺名称" />
        </el-form-item>
        
        <el-form-item label="平台" prop="platform">
          <el-select v-model="form.platform" placeholder="请选择平台" style="width: 100%">
            <el-option label="拼多多" value="pinduoduo" />
            <el-option label="淘宝" value="taobao" />
            <el-option label="京东" value="jd" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="active">运行中</el-radio>
            <el-radio label="inactive">已停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStoreStore } from '@/stores/store'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const storeStore = useStoreStore()

const loading = computed(() => storeStore.loading)
const stores = computed(() => storeStore.stores)

// 对话框状态
const showCreateDialog = ref(false)
const editingStore = ref(null)
const submitting = ref(false)
const formRef = ref(null)

// 表单数据
const form = reactive({
  name: '',
  platform: '',
  status: 'active'
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入店铺名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  platform: [
    { required: true, message: '请选择平台', trigger: 'change' }
  ]
}

// 获取平台标签类型
const getPlatformType = (platform) => {
  const types = {
    pinduoduo: 'danger',
    taobao: 'warning',
    jd: 'primary'
  }
  return types[platform] || 'info'
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 进入店铺管理
const goToStore = (store) => {
  storeStore.setCurrentStore(store)
  router.push(`/stores/${store.id}`)
}

// 编辑店铺
const handleEdit = (store) => {
  editingStore.value = store
  form.name = store.name
  form.platform = store.platform
  form.status = store.status || 'active'
  showCreateDialog.value = true
}

// 删除店铺
const handleDelete = async (store) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除店铺"${store.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await storeStore.deleteStoreAction(store.id)
    ElMessage.success('店铺已删除')
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
    if (editingStore.value) {
      // 更新店铺
      await storeStore.updateStoreAction(editingStore.value.id, form)
      ElMessage.success('店铺已更新')
    } else {
      // 创建店铺
      await storeStore.createStoreAction(form)
      ElMessage.success('店铺已创建')
    }
    showCreateDialog.value = false
    resetForm()
  } catch (error) {
    // 错误已由 axios 拦截器处理
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  form.name = ''
  form.platform = ''
  form.status = 'active'
  editingStore.value = null
  formRef.value?.resetFields()
}

// 加载数据
onMounted(async () => {
  await storeStore.fetchStores()
})
</script>

<style scoped>
.stores-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.header-left p {
  color: #909399;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 8px;
}

.empty-icon {
  font-size: 64px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.store-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 20px;
}

.store-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.store-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.store-name {
  font-size: 18px;
  color: #303133;
  margin-bottom: 16px;
}

.store-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.info-item .label {
  color: #909399;
}

.store-stats {
  display: flex;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-item .value {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.stat-item .label {
  font-size: 12px;
  color: #909399;
}
</style>
