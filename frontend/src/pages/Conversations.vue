<template>
  <div class="conversations-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>对话记录</h2>
        <p v-if="currentStore">{{ currentStore.name }} - 对话记录</p>
      </div>
      <div class="header-right">
        <el-select v-model="filterStatus" placeholder="筛选状态" style="width: 120px" @change="handleFilterChange">
          <el-option label="全部" value="" />
          <el-option label="进行中" value="active" />
          <el-option label="已关闭" value="closed" />
        </el-select>
      </div>
    </div>

    <!-- 对话列表 -->
    <div class="page-card" v-loading="loading">
      <el-table :data="conversations" style="width: 100%" @row-click="goToDetail">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="customer" label="客户" min-width="120" />
        <el-table-column prop="lastMessage" label="最后消息" min-width="250" show-overflow-tooltip />
        <el-table-column prop="messageCount" label="消息数" width="100" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '进行中' : '已关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="最后更新" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updatedAt) }}
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && conversations.length === 0" description="暂无对话记录" />

      <!-- 分页 -->
      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStoreStore } from '@/stores/store'
import { getConversations } from '@/api/conversations'

const router = useRouter()
const storeStore = useStoreStore()

const currentStore = computed(() => storeStore.currentStore)
const currentStoreId = computed(() => storeStore.currentStoreId)

// 列表数据
const loading = ref(false)
const conversations = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const filterStatus = ref('')

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  const now = new Date()
  const date = new Date(dateStr)
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return formatDate(dateStr)
}

// 加载对话列表
const loadConversations = async () => {
  if (!currentStoreId.value) return
  
  loading.value = true
  try {
    const res = await getConversations(currentStoreId.value, {
      status: filterStatus.value,
      page: currentPage.value,
      limit: pageSize.value
    })
    conversations.value = res.items || res.list || res || []
    total.value = res.total || conversations.value.length
  } catch (error) {
    console.error('加载对话列表失败:', error)
    // 使用模拟数据
    conversations.value = generateMockData()
    total.value = 25
  } finally {
    loading.value = false
  }
}

// 生成模拟数据
const generateMockData = () => {
  const customers = ['用户_张三', '用户_李四', '用户_王五', '用户_赵六', '用户_钱七']
  const messages = [
    '请问这款商品有优惠吗？',
    '什么时候能发货？',
    '退换货怎么操作？',
    '收到货了，很满意！',
    '质量不错，下次还来'
  ]
  const statuses = ['active', 'closed']
  
  return Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    customer: customers[i % customers.length],
    lastMessage: messages[i % messages.length],
    messageCount: Math.floor(Math.random() * 20) + 1,
    status: statuses[i % 2],
    createdAt: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString(),
    updatedAt: new Date(Date.now() - Math.random() * 3600000).toISOString()
  }))
}

// 跳转到详情
const goToDetail = (row) => {
  router.push(`/conversations/${row.id}`)
}

// 筛选变化
const handleFilterChange = () => {
  currentPage.value = 1
  loadConversations()
}

// 分页变化
const handlePageChange = () => {
  loadConversations()
}

const handleSizeChange = () => {
  currentPage.value = 1
  loadConversations()
}

// 监听店铺变化
watch(currentStoreId, (newVal) => {
  if (newVal) {
    loadConversations()
  }
})

onMounted(() => {
  if (currentStoreId.value) {
    loadConversations()
  }
})
</script>

<style scoped>
.conversations-page {
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

.page-card :deep(.el-table__row) {
  cursor: pointer;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
