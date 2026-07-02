<template>
  <div class="store-detail-page" v-loading="loading">
    <div class="page-header">
      <el-button text @click="$router.push('/stores')">
        <el-icon><ArrowLeft /></el-icon>
        返回店铺列表
      </el-button>
    </div>

    <div v-if="store" class="store-detail">
      <!-- 店铺信息卡片 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <div>
              <h2>{{ store.name }}</h2>
              <el-tag :type="getPlatformType(store.platform)" size="large">
                {{ getPlatformName(store.platform) }}
              </el-tag>
              <el-tag :type="store.status === 'active' ? 'success' : 'info'" style="margin-left: 8px;">
                {{ store.status === 'active' ? '运行中' : '已停用' }}
              </el-tag>
            </div>
            <el-button type="primary" @click="showEditDialog = true">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </div>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="店铺ID">{{ store.id }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(store.createdAt) }}</el-descriptions-item>
          <el-descriptions-item label="对话数量">{{ store.conversationCount || 0 }}</el-descriptions-item>
          <el-descriptions-item label="知识条目">{{ store.knowledgeCount || 0 }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 快捷操作 -->
      <el-row :gutter="20" class="quick-actions">
        <el-col :span="8">
          <el-card class="action-card" @click="$router.push('/knowledge')">
            <div class="action-content">
              <el-icon class="action-icon"><Document /></el-icon>
              <span>管理知识库</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="action-card" @click="$router.push('/conversations')">
            <div class="action-content">
              <el-icon class="action-icon"><ChatDotRound /></el-icon>
              <span>查看对话</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="action-card" @click="$router.push('/settings')">
            <div class="action-content">
              <el-icon class="action-icon"><Setting /></el-icon>
              <span>店铺设置</span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 店铺统计 -->
      <el-card class="stats-card">
        <template #header>
          <span>今日数据</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.todayConversations }}</div>
              <div class="stat-label">今日对话</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.todayMessages }}</div>
              <div class="stat-label">今日消息</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.avgResponseTime }}s</div>
              <div class="stat-label">平均响应</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.satisfaction }}%</div>
              <div class="stat-label">满意度</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑店铺" width="500px">
      <el-form ref="formRef" :model="editForm" :rules="rules" label-width="80px">
        <el-form-item label="店铺名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入店铺名称" />
        </el-form-item>
        
        <el-form-item label="平台" prop="platform">
          <el-select v-model="editForm.platform" placeholder="请选择平台" style="width: 100%">
            <el-option label="拼多多" value="pinduoduo" />
            <el-option label="淘宝" value="taobao" />
            <el-option label="京东" value="jd" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="editForm.status">
            <el-radio label="active">运行中</el-radio>
            <el-radio label="inactive">已停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useStoreStore } from '@/stores/store'
import { ElMessage } from 'element-plus'

const route = useRoute()
const storeStore = useStoreStore()

const loading = computed(() => storeStore.loading)
const store = computed(() => storeStore.currentStore)

// 编辑相关
const showEditDialog = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const editForm = reactive({
  name: '',
  platform: '',
  status: 'active'
})

const rules = {
  name: [
    { required: true, message: '请输入店铺名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  platform: [
    { required: true, message: '请选择平台', trigger: 'change' }
  ]
}

// 统计数据
const stats = reactive({
  todayConversations: 0,
  todayMessages: 0,
  avgResponseTime: 0,
  satisfaction: 0
})

// 获取平台名称
const getPlatformName = (platform) => {
  const names = {
    pinduoduo: '拼多多',
    taobao: '淘宝',
    jd: '京东'
  }
  return names[platform] || platform
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

// 加载店铺数据
const loadStore = async () => {
  const id = route.params.id
  await storeStore.fetchStore(id)
  
  // 更新编辑表单
  if (store.value) {
    editForm.name = store.value.name
    editForm.platform = store.value.platform
    editForm.status = store.value.status || 'active'
    
    // 设置为当前店铺
    storeStore.setCurrentStore(store.value)
  }
  
  // 获取统计数据
  const storeStats = await storeStore.fetchStats(id)
  if (storeStats) {
    Object.assign(stats, storeStats)
  }
}

// 更新店铺
const handleUpdate = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await storeStore.updateStoreAction(route.params.id, editForm)
    ElMessage.success('店铺已更新')
    showEditDialog.value = false
  } catch (error) {
    // 错误已由 axios 拦截器处理
  } finally {
    submitting.value = false
  }
}

// 监听路由变化
watch(() => route.params.id, () => {
  if (route.params.id) {
    loadStore()
  }
})

onMounted(() => {
  loadStore()
})
</script>

<style scoped>
.store-detail-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.store-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.card-header h2 {
  margin: 0 0 12px 0;
  font-size: 20px;
}

.quick-actions .el-col {
  cursor: pointer;
}

.action-card {
  text-align: center;
}

.action-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
}

.action-icon {
  font-size: 36px;
  color: #409eff;
}

.stats-card .stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}
</style>
