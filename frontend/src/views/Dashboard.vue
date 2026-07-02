<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ stats.storeCount || 0 }}</div>
          <div class="stat-label">店铺数量</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ stats.todayConversations || 0 }}</div>
          <div class="stat-label">今日对话</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ stats.todayMessages || 0 }}</div>
          <div class="stat-label">今日消息</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ stats.knowledgeCount || 0 }}</div>
          <div class="stat-label">知识库条目</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header><span>快捷操作</span></template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/stores')">管理店铺</el-button>
            <el-button type="success" @click="$router.push('/knowledge')">编辑知识库</el-button>
            <el-button type="warning" @click="$router.push('/conversations')">查看对话</el-button>
            <el-button @click="$router.push('/settings')">系统设置</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>最近对话</span></template>
          <el-table :data="recentConversations" size="small" style="width: 100%">
            <el-table-column prop="customer_name" label="客户" width="100" />
            <el-table-column prop="last_message" label="最新消息" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '进行中' : '已关闭' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!recentConversations.length" description="暂无对话" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import api from '@/utils/request'

const appStore = useAppStore()
const stats = ref({})
const recentConversations = ref([])

onMounted(async () => {
  try {
    const data = await api.get('/info')
    stats.value = {
      storeCount: appStore.stores.length,
      todayConversations: data.today_conversations || 0,
      todayMessages: data.today_messages || 0,
      knowledgeCount: data.knowledge_count || 0
    }
  } catch (e) {
    stats.value = { storeCount: appStore.stores.length }
  }

  // 获取最近对话
  if (appStore.currentStoreId) {
    try {
      const data = await api.get(`/stores/${appStore.currentStoreId}/conversations?limit=5`)
      recentConversations.value = data || []
    } catch (e) {}
  }
})
</script>

<style scoped>
.stat-row .el-col { margin-bottom: 0; }
.stat-card { text-align: center; }
.stat-number { font-size: 32px; font-weight: bold; color: #409EFF; }
.stat-label { font-size: 14px; color: #999; margin-top: 8px; }
.quick-actions { display: flex; flex-wrap: wrap; gap: 12px; }
</style>
