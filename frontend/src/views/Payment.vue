<template>
  <div class="payment-page">
    <div class="payment-card">
      <div class="payment-header">
        <h2>💎 开通会员</h2>
        <p class="subtitle">解锁全部功能，畅享智能客服</p>
      </div>

      <!-- 当前状态 -->
      <div v-if="paymentStatus" class="status-bar" :class="{ active: paymentStatus.paid }">
        <el-icon v-if="paymentStatus.paid"><CircleCheck /></el-icon>
        <el-icon v-else><Warning /></el-icon>
        <span v-if="paymentStatus.paid">
          当前套餐：<strong>{{ planLabel }}</strong>
          <span v-if="paymentStatus.paid_type === 'permanent'">（永久有效）</span>
          <span v-else> · 到期时间：{{ formatDate(paymentStatus.expires_at) }}</span>
        </span>
        <span v-else>
          <template v-if="paymentStatus.paid_type === 'free'">
            免费试用中 · 到期时间：{{ formatDate(paymentStatus.expires_at) }}
          </template>
          <template v-else>
            会员已过期，请续费
          </template>
        </span>
      </div>

      <!-- 套餐选择 -->
      <div class="plans" v-if="!paymentStatus?.paid">
        <div
          v-for="(info, key) in planInfo"
          :key="key"
          class="plan-card"
          :class="{ selected: selectedPlan === key }"
          @click="selectedPlan = key"
        >
          <div class="plan-badge" v-if="key === 'yearly'">推荐</div>
          <div class="plan-icon">{{ info.icon }}</div>
          <div class="plan-name">{{ info.label }}</div>
          <div class="plan-price">
            <span class="currency">¥</span>
            <span class="amount">{{ info.price }}</span>
            <span class="unit">/{{ info.unit }}</span>
          </div>
          <div class="plan-desc">{{ info.desc }}</div>
        </div>
      </div>

      <!-- 支付按钮 -->
      <div class="pay-action" v-if="!paymentStatus?.paid">
        <el-button
          type="primary"
          size="large"
          :loading="paying"
          @click="handlePay"
          :disabled="!selectedPlan"
          style="width: 100%; height: 48px; font-size: 16px;"
        >
          {{ paying ? '正在创建订单...' : `立即支付 ¥${currentPrice}` }}
        </el-button>
        <p class="pay-tip">支付成功后自动开通，支持微信/支付宝</p>
      </div>

      <!-- 支付弹窗 -->
      <el-dialog v-model="payDialogVisible" title="扫码支付" width="400px" :close-on-click-modal="false">
        <div class="pay-dialog-content">
          <div v-if="payUrl" class="qr-wrapper">
            <p class="pay-amount">¥{{ payAmount }}</p>
            <div class="qr-frame">
              <img :src="qrCodeUrl" alt="支付二维码" class="qr-image" />
            </div>
            <p class="pay-methods">支持微信 / 支付宝扫码支付</p>
            <el-button type="primary" link @click="checkPayStatus">
              <el-icon><Refresh /></el-icon> 我已支付，点击确认
            </el-button>
          </div>
          <div v-else class="pay-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <p>正在加载支付二维码...</p>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CircleCheck, Warning, Refresh, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import paymentApi from '@/api/payment'

const paymentStatus = ref(null)
const prices = ref({})
const selectedPlan = ref('monthly')
const paying = ref(false)
const payDialogVisible = ref(false)
const payUrl = ref('')
const payAmount = ref(0)
const currentOrderId = ref('')
let checkTimer = null

const planInfo = computed(() => {
  const p = prices.value.prices || {}
  return {
    monthly: {
      icon: '🌙',
      label: '月度会员',
      price: p.monthly || 99,
      unit: '月',
      desc: '有效期 30 天',
    },
    yearly: {
      icon: '👑',
      label: '年度会员',
      price: p.yearly || 666,
      unit: '年',
      desc: '有效期 365 天，省 ¥122',
    },
  }
})

const currentPrice = computed(() => planInfo.value[selectedPlan.value]?.price || 0)

const planLabel = computed(() => {
  if (!paymentStatus.value) return ''
  const type = paymentStatus.value.paid_type
  const labels = { monthly: '月度会员', yearly: '年度会员', permanent: '永久会员', free: '免费试用' }
  return labels[type] || type
})

const qrCodeUrl = computed(() => {
  if (!payUrl.value) return ''
  return `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(payUrl.value)}&size=200x200`
})

function formatDate(isoStr) {
  if (!isoStr) return '-'
  try {
    const d = new Date(isoStr)
    return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch { return isoStr }
}

async function loadStatus() {
  try {
    const res = await paymentApi.getStatus()
    paymentStatus.value = res
  } catch (e) {
    console.error('加载付费状态失败', e)
  }
}

async function loadPrices() {
  try {
    const res = await paymentApi.getPrices()
    prices.value = res
  } catch (e) {
    console.error('加载价格失败', e)
  }
}

async function handlePay() {
  paying.value = true
  try {
    const res = await paymentApi.createPayment({ plan: selectedPlan.value })
    if (res.already_paid) {
      ElMessage.success('您已经付费过了')
      loadStatus()
      return
    }
    currentOrderId.value = res.order_id
    payUrl.value = res.pay_url
    payAmount.value = res.amount
    payDialogVisible.value = true
    // 自动轮询支付状态
    startCheckTimer()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建订单失败')
  } finally {
    paying.value = false
  }
}

function startCheckTimer() {
  if (checkTimer) clearInterval(checkTimer)
  checkTimer = setInterval(async () => {
    try {
      const res = await paymentApi.checkOrder(currentOrderId.value)
      if (res.status === 'paid') {
        clearInterval(checkTimer)
        checkTimer = null
        payDialogVisible.value = false
        ElMessage.success('支付成功！会员已开通')
        loadStatus()
      }
    } catch {}
  }, 3000)
}

async function checkPayStatus() {
  try {
    const res = await paymentApi.checkOrder(currentOrderId.value)
    if (res.status === 'paid') {
      if (checkTimer) clearInterval(checkTimer)
      payDialogVisible.value = false
      ElMessage.success('支付成功！会员已开通')
      loadStatus()
    } else {
      ElMessage.info('订单尚未支付，请完成支付后再确认')
    }
  } catch (e) {
    ElMessage.error('查询失败，请稍后重试')
  }
}

onMounted(() => {
  loadStatus()
  loadPrices()
})
</script>

<style scoped>
.payment-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}
.payment-card {
  width: 560px;
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.15);
}
.payment-header {
  text-align: center;
  margin-bottom: 24px;
}
.payment-header h2 {
  font-size: 24px;
  margin-bottom: 8px;
}
.subtitle {
  color: #999;
  font-size: 14px;
}
.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  background: #fef0f0;
  color: #f56c6c;
  margin-bottom: 24px;
  font-size: 14px;
}
.status-bar.active {
  background: #f0f9eb;
  color: #67c23a;
}
.plans {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.plan-card {
  flex: 1;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}
.plan-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
}
.plan-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}
.plan-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #e6a23c;
  color: #fff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}
.plan-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
.plan-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.plan-price {
  margin-bottom: 8px;
}
.currency {
  font-size: 16px;
  color: #f56c6c;
}
.amount {
  font-size: 32px;
  font-weight: 700;
  color: #f56c6c;
}
.unit {
  font-size: 14px;
  color: #999;
}
.plan-desc {
  font-size: 12px;
  color: #999;
}
.pay-action {
  text-align: center;
}
.pay-tip {
  font-size: 12px;
  color: #999;
  margin-top: 12px;
}
.pay-dialog-content {
  text-align: center;
}
.pay-amount {
  font-size: 28px;
  font-weight: 700;
  color: #f56c6c;
  margin-bottom: 16px;
}
.qr-frame {
  display: inline-block;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}
.qr-image {
  width: 200px;
  height: 200px;
}
.pay-methods {
  margin: 16px 0 12px;
  color: #999;
  font-size: 13px;
}
.pay-loading {
  padding: 40px 0;
  color: #999;
}
.pay-loading .el-icon {
  font-size: 32px;
}
</style>
