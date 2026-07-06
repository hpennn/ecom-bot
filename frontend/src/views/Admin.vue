<template>
  <div class="admin-page">
    <!-- 顶部统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_users }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">💎</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.paid_users }}</div>
          <div class="stat-label">付费用户</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.paid_rate }}%</div>
          <div class="stat-label">付费率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">💰</div>
        <div class="stat-info">
          <div class="stat-value">¥{{ stats.monthly_income }}</div>
          <div class="stat-label">本月收入</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏦</div>
        <div class="stat-info">
          <div class="stat-value">¥{{ stats.total_income }}</div>
          <div class="stat-label">总收入</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_orders }}</div>
          <div class="stat-label">总订单</div>
        </div>
      </div>
    </div>

    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" class="admin-tabs">
      <!-- 用户管理 -->
      <el-tab-pane label="👥 用户管理" name="users">
        <el-table :data="users" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="email" label="邮箱" width="180" />
          <el-table-column label="付费状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getPaidTagType(row.paid_type)" size="small">
                {{ getPaidLabel(row.paid_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '有效' : '过期' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="expires_at" label="到期时间" width="160">
            <template #default="{ row }">
              {{ row.expires_at ? formatDate(row.expires_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="管理员" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.is_admin" type="warning" size="small">管理员</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <el-dropdown trigger="click" @command="(cmd) => handleUserAction(row, cmd)">
                <el-button size="small" type="primary" link>修改套餐</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="free">免费用户</el-dropdown-item>
                    <el-dropdown-item command="monthly">月度会员</el-dropdown-item>
                    <el-dropdown-item command="yearly">年度会员</el-dropdown-item>
                    <el-dropdown-item command="permanent">永久会员</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button
                size="small"
                :type="row.is_admin ? 'warning' : 'default'"
                link
                @click="toggleAdmin(row)"
                style="margin-left: 8px"
              >
                {{ row.is_admin ? '取消管理员' : '设为管理员' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 订单管理 -->
      <el-tab-pane label="📋 订单管理" name="orders">
        <el-table :data="orders" stripe style="width: 100%">
          <el-table-column prop="order_id" label="订单号" width="200" />
          <el-table-column prop="username" label="用户" width="120" />
          <el-table-column label="金额" width="100">
            <template #default="{ row }">
              <span style="color: #f56c6c; font-weight: 600;">¥{{ row.amount }}</span>
            </template>
          </el-table-column>
          <el-table-column label="套餐" width="100">
            <template #default="{ row }">
              {{ getPaidLabel(row.paid_type) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'paid' ? 'success' : 'warning'" size="small">
                {{ row.status === 'paid' ? '已支付' : '待支付' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="paid_at" label="支付时间" width="160">
            <template #default="{ row }">
              {{ row.paid_at ? formatDate(row.paid_at) : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import adminApi from '@/api/admin'

const activeTab = ref('users')
const stats = ref({
  total_users: 0, paid_users: 0, free_users: 0,
  paid_rate: 0, monthly_income: 0, total_income: 0,
  total_orders: 0, paid_orders: 0,
})
const users = ref([])
const orders = ref([])

function getPaidLabel(type) {
  const labels = { free: '免费', monthly: '月度', yearly: '年度', permanent: '永久' }
  return labels[type] || type
}

function getPaidTagType(type) {
  const types = { free: 'info', monthly: '', yearly: 'warning', permanent: 'danger' }
  return types[type] || 'info'
}

function formatDate(isoStr) {
  if (!isoStr) return '-'
  try {
    const d = new Date(isoStr)
    return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch { return isoStr }
}

async function loadStats() {
  try {
    stats.value = await adminApi.getStats()
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

async function loadUsers() {
  try {
    const res = await adminApi.getUsers()
    users.value = res.users || []
  } catch (e) {
    console.error('加载用户失败', e)
  }
}

async function loadOrders() {
  try {
    const res = await adminApi.getOrders()
    orders.value = res.orders || []
  } catch (e) {
    console.error('加载订单失败', e)
  }
}

async function handleUserAction(row, paidType) {
  try {
    await adminApi.updateUser(row.id, { paid_type: paidType })
    ElMessage.success(`已将 ${row.username} 设为 ${getPaidLabel(paidType)}`)
    loadUsers()
    loadStats()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function toggleAdmin(row) {
  const action = row.is_admin ? '取消' : '授予'
  try {
    await ElMessageBox.confirm(
      `确定要${action} ${row.username} 的管理员权限吗？`,
      '确认操作',
      { type: 'warning' }
    )
    await adminApi.setAdmin(row.id, { is_admin: !row.is_admin })
    ElMessage.success(`${action}管理员成功`)
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

onMounted(() => {
  loadStats()
  loadUsers()
  loadOrders()
})
</script>

<style scoped>
.admin-page {
  padding: 0;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stat-icon {
  font-size: 36px;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.admin-tabs {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
}
</style>
