<template>
  <div class="page-container">
    <h2>📊 数据统计</h2>

    <!-- 概览卡片 -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <div class="stat-card total">
          <div class="stat-value">{{ overview.today?.total_messages || 0 }}</div>
          <div class="stat-label">今日消息数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card hit">
          <div class="stat-value">{{ overview.today?.hit_rate || 0 }}%</div>
          <div class="stat-label">知识库命中率</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card transfer">
          <div class="stat-value">{{ overview.today?.transfer_replies || 0 }}</div>
          <div class="stat-label">今日转人工</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card customers">
          <div class="stat-value">{{ overview.today?.unique_customers || 0 }}</div>
          <div class="stat-label">今日客户数</div>
        </div>
      </el-col>
    </el-row>

    <!-- 周/月汇总 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>本周统计</template>
          <div class="summary-row"><span>总消息</span><strong>{{ overview.this_week?.total_messages || 0 }}</strong></div>
          <div class="summary-row"><span>关键词回复</span><strong>{{ overview.this_week?.keyword_replies || 0 }}</strong></div>
          <div class="summary-row"><span>知识库回复</span><strong>{{ overview.this_week?.knowledge_replies || 0 }}</strong></div>
          <div class="summary-row"><span>AI回复</span><strong>{{ overview.this_week?.ai_replies || 0 }}</strong></div>
          <div class="summary-row"><span>转人工</span><strong>{{ overview.this_week?.transfer_replies || 0 }}</strong></div>
          <div class="summary-row highlight"><span>命中率</span><strong>{{ overview.this_week?.hit_rate || 0 }}%</strong></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>本月统计</template>
          <div class="summary-row"><span>总消息</span><strong>{{ overview.this_month?.total_messages || 0 }}</strong></div>
          <div class="summary-row"><span>关键词回复</span><strong>{{ overview.this_month?.keyword_replies || 0 }}</strong></div>
          <div class="summary-row"><span>知识库回复</span><strong>{{ overview.this_month?.knowledge_replies || 0 }}</strong></div>
          <div class="summary-row"><span>AI回复</span><strong>{{ overview.this_month?.ai_replies || 0 }}</strong></div>
          <div class="summary-row"><span>转人工</span><strong>{{ overview.this_month?.transfer_replies || 0 }}</strong></div>
          <div class="summary-row highlight"><span>命中率</span><strong>{{ overview.this_month?.hit_rate || 0 }}%</strong></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 每日趋势 -->
    <el-card shadow="hover" style="margin-top: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>近7天趋势</span>
          <el-radio-group v-model="trendDays" size="small" @change="loadDaily">
            <el-radio-button :value="7">7天</el-radio-button>
            <el-radio-button :value="14">14天</el-radio-button>
            <el-radio-button :value="30">30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div class="chart-container">
        <div class="bar-chart">
          <div v-for="d in dailyData" :key="d.date" class="bar-group">
            <div class="bar-stack">
              <div class="bar kw" :style="{ height: barHeight(d.keyword_replies, 'kw') + 'px' }" :title="'关键词: ' + d.keyword_replies"></div>
              <div class="bar know" :style="{ height: barHeight(d.knowledge_replies, 'know') + 'px' }" :title="'知识库: ' + d.knowledge_replies"></div>
              <div class="bar ai" :style="{ height: barHeight(d.ai_replies, 'ai') + 'px' }" :title="'AI: ' + d.ai_replies"></div>
              <div class="bar transfer" :style="{ height: barHeight(d.transfer_replies, 'transfer') + 'px' }" :title="'转人工: ' + d.transfer_replies"></div>
            </div>
            <div class="bar-label">{{ d.date.slice(5) }}</div>
            <div class="bar-total">{{ d.total_messages }}</div>
          </div>
        </div>
        <div class="chart-legend">
          <span class="legend-item"><i class="dot kw"></i>关键词</span>
          <span class="legend-item"><i class="dot know"></i>知识库</span>
          <span class="legend-item"><i class="dot ai"></i>AI生成</span>
          <span class="legend-item"><i class="dot transfer"></i>转人工</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '@/utils/request'

const overview = ref({})
const dailyData = ref([])
const trendDays = ref(7)
const storeId = 1

const maxVal = computed(() => Math.max(1, ...dailyData.value.map(d => d.total_messages)))

const barHeight = (val, type) => {
  const total = maxVal.value
  return Math.max(2, (val / total) * 150)
}

const loadOverview = async () => {
  const res = await request.get('/api/stats/overview', { params: { store_id: storeId } })
  overview.value = res.data
}

const loadDaily = async () => {
  const res = await request.get(`/api/stats/${storeId}/daily`, { params: { days: trendDays.value } })
  dailyData.value = res.data.data
}

onMounted(() => {
  loadOverview()
  loadDaily()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.stat-cards { margin-bottom: 16px; }
.stat-card { background: #fff; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #eee; }
.stat-card.total { border-left: 4px solid #409EFF; }
.stat-card.hit { border-left: 4px solid #67C23A; }
.stat-card.transfer { border-left: 4px solid #E6A23C; }
.stat-card.customers { border-left: 4px solid #F56C6C; }
.stat-value { font-size: 28px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.summary-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.summary-row:last-child { border: none; }
.summary-row.highlight { color: #67C23A; font-weight: 600; }
.chart-container { padding: 10px 0; }
.bar-chart { display: flex; align-items: flex-end; justify-content: space-around; height: 200px; padding: 0 10px; }
.bar-group { display: flex; flex-direction: column; align-items: center; flex: 1; }
.bar-stack { display: flex; flex-direction: column-reverse; align-items: center; }
.bar { width: 24px; margin: 1px 0; border-radius: 2px; transition: height 0.3s; }
.bar.kw { background: #409EFF; }
.bar.know { background: #67C23A; }
.bar.ai { background: #E6A23C; }
.bar.transfer { background: #F56C6C; }
.bar-label { font-size: 11px; color: #909399; margin-top: 4px; }
.bar-total { font-size: 11px; color: #606266; font-weight: 600; }
.chart-legend { display: flex; justify-content: center; gap: 16px; margin-top: 12px; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #606266; }
.dot { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.dot.kw { background: #409EFF; }
.dot.know { background: #67C23A; }
.dot.ai { background: #E6A23C; }
.dot.transfer { background: #F56C6C; }
</style>
