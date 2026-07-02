<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>仪表盘</h2>
      <p>欢迎回来，{{ username }}！以下是您的数据概览。</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="page-card stat-card">
          <div class="stat-icon">
            <el-icon><Shop /></el-icon>
          </div>
          <div class="stat-value">{{ stats.storeCount }}</div>
          <div class="stat-label">店铺数量</div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="page-card stat-card">
          <div class="stat-icon">
            <el-icon><ChatLineRound /></el-icon>
          </div>
          <div class="stat-value">{{ stats.todayConversations }}</div>
          <div class="stat-label">今日对话数</div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="page-card stat-card">
          <div class="stat-icon">
            <el-icon><Message /></el-icon>
          </div>
          <div class="stat-value">{{ stats.todayMessages }}</div>
          <div class="stat-label">今日消息数</div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="page-card stat-card">
          <div class="stat-icon ai">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stat-value">{{ stats.aiReplyRate }}%</div>
          <div class="stat-label">AI回复率</div>
        </div>
      </el-col>
    </el-row>

    <!-- 知识库统计 & 最近对话 -->
    <el-row :gutter="20">
      <!-- 知识库统计 -->
      <el-col :xs="24" :md="8">
        <div class="page-card knowledge-stats">
          <h3>知识库统计</h3>
          <div class="knowledge-item">
            <span>FAQ</span>
            <el-tag type="info">{{ knowledgeStats.faq }}</el-tag>
          </div>
          <div class="knowledge-item">
            <span>商品信息</span>
            <el-tag type="success">{{ knowledgeStats.product }}</el-tag>
          </div>
          <div class="knowledge-item">
            <span>售后政策</span>
            <el-tag type="warning">{{ knowledgeStats.afterSales }}</el-tag>
          </div>
          <div class="knowledge-item">
            <span>物流信息</span>
            <el-tag>{{ knowledgeStats.logistics }}</el-tag>
          </div>
          <div class="knowledge-item">
            <span>自定义</span>
            <el-tag type="danger">{{ knowledgeStats.custom }}</el-tag>
          </div>
          <div class="knowledge-total">
            <span>总计</span>
            <strong>{{ knowledgeStats.total }}</strong>
          </div>
          <el-button type="primary" @click="$router.push('/knowledge')">
            管理知识库
          </el-button>
        </div>
      </el-col>

      <!-- 最近对话 -->
      <el-col :xs="24" :md="16">
        <div class="page-card recent-conversations">
          <div class="section-header">
            <h3>最近对话</h3>
            <el-button text @click="$router.push('/conversations')">
              查看更多
            </el-button>
          </div>
          
          <el-table :data="recentConversations" style="width: 100%" v-loading="loading">
            <el-table-column prop="customer" label="客户" min-width="100" />
            <el-table-column prop="lastMessage" label="最后消息" min-width="200" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === '进行中' ? 'success' : 'info'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="time" label="时间" width="160" />
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button 
                  type="primary" 
                  text 
                  size="small"
                  @click="viewConversation(row)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!loading && recentConversations.length === 0" description="暂无对话记录" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useStoreStore } from '@/stores/store'
import { useKnowledgeStore } from '@/stores/knowledge'

const router = useRouter()
const authStore = useAuthStore()
const storeStore = useStoreStore()
const knowledgeStore = useKnowledgeStore()

const loading = ref(false)

// 用户信息
const username = computed(() => authStore.username)

// 统计数据
const stats = reactive({
  storeCount: 0,
  todayConversations: 0,
  todayMessages: 0,
  aiReplyRate: 0
})

// 知识库统计
const knowledgeStats = reactive({
  faq: 0,
  product: 0,
  afterSales: 0,
  logistics: 0,
  custom: 0,
  total: 0
})

// 最近对话
const recentConversations = ref([])

// 查看对话
const viewConversation = (row) => {
  router.push(`/conversations/${row.id}`)
}

// 加载仪表盘数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    // 获取店铺列表
    await storeStore.fetchStores()
    stats.storeCount = storeStore.storeCount

    // 如果有当前店铺，获取其统计数据
    if (storeStore.currentStoreId) {
      const storeStats = await storeStore.fetchStats(storeStore.currentStoreId)
      if (storeStats) {
        stats.todayConversations = storeStats.todayConversations || 0
        stats.todayMessages = storeStats.todayMessages || 0
        stats.aiReplyRate = storeStats.aiReplyRate || 0
      }
      
      // 获取知识库统计
      await knowledgeStore.fetchKnowledgeList(storeStore.currentStoreId)
      knowledgeStats.faq = knowledgeStore.faqCount
      knowledgeStats.product = knowledgeStore.productCount
      knowledgeStats.afterSales = knowledgeStore.afterSalesCount
      knowledgeStats.logistics = knowledgeStore.logisticsCount
      knowledgeStats.custom = knowledgeStore.total - 
        (knowledgeStats.faq + knowledgeStats.product + knowledgeStats.afterSales + knowledgeStats.logistics)
      knowledgeStats.total = knowledgeStore.total
    }

    // 模拟最近对话数据（实际应从API获取）
    recentConversations.value = [
      { id: 1, customer: '用户_张三', lastMessage: '请问这款商品有优惠吗？', status: '进行中', time: '10分钟前' },
      { id: 2, customer: '用户_李四', lastMessage: '好的，谢谢！', status: '已关闭', time: '30分钟前' },
      { id: 3, customer: '用户_王五', lastMessage: '什么时候能发货？', status: '进行中', time: '1小时前' },
      { id: 4, customer: '用户_赵六', lastMessage: '退换货怎么操作？', status: '已关闭', time: '2小时前' },
      { id: 5, customer: '用户_钱七', lastMessage: '收到货了，很满意！', status: '已关闭', time: '3小时前' }
    ]
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.page-header p {
  color: #909399;
  font-size: 14px;
}

.stat-cards {
  margin-bottom: 20px;
}

.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stat-card {
  text-align: center;
  height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 12px;
}

.stat-icon.ai {
  color: #67c23a;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.knowledge-stats h3,
.recent-conversations h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 16px;
}

.knowledge-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.knowledge-item:last-of-type {
  border-bottom: none;
}

.knowledge-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  margin-bottom: 16px;
  border-top: 2px solid #409eff;
  font-size: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin-bottom: 0;
}
</style>
