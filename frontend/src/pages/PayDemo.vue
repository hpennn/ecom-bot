<template>
  <div class="pay-demo-container">
    <el-card class="pay-card">
      <template #header>
        <div class="card-header">
          <span>支付测试</span>
          <el-button type="primary" @click="loadPayConfig">
            刷新配置
          </el-button>
        </div>
      </template>

      <!-- 支付配置信息 -->
      <div class="config-info">
        <h4>微信支付配置</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="商户号">
            {{ payConfig.mch_id || '未配置' }}
          </el-descriptions-item>
          <el-descriptions-item label="AppID">
            {{ payConfig.app_id || '待配置' }}
          </el-descriptions-item>
          <el-descriptions-item label="JSAPI可用">
            <el-tag :type="payConfig.jsapi_available ? 'success' : 'warning'" size="small">
              {{ payConfig.jsapi_available ? '可用' : '不可用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支付超时">
            {{ payConfig.pay_timeout ? payConfig.pay_timeout / 60 + '分钟' : '未配置' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 创建订单表单 -->
      <el-divider>创建支付订单</el-divider>
      
      <el-form :model="orderForm" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="商品描述" prop="description">
          <el-input 
            v-model="orderForm.description" 
            placeholder="请输入商品描述"
            maxlength="127"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="支付金额" prop="amount">
          <el-input-number 
            v-model="orderForm.amountYuan" 
            :min="0.01" 
            :max="10000" 
            :precision="2"
            controls-position="right"
          />
          <span class="amount-tip">（单位：元）</span>
        </el-form-item>
        
        <el-form-item label="支付方式" prop="payType">
          <el-radio-group v-model="orderForm.payType">
            <el-radio label="native">扫码支付（Native）</el-radio>
            <el-radio label="jsapi" :disabled="!payConfig.jsapi_available">
              JSAPI支付
            </el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="用户OpenID" v-if="orderForm.payType === 'jsapi'">
          <el-input 
            v-model="orderForm.openid" 
            placeholder="请输入用户OpenID"
          />
        </el-form-item>
        
        <el-form-item label="附加数据">
          <el-input 
            v-model="orderForm.attach" 
            placeholder="可选，用于自定义数据"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleCreateOrder" :loading="creating">
            创建订单并支付
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 订单历史 -->
    <el-card class="orders-card" v-if="orderHistory.length > 0">
      <template #header>
        <span>订单历史</span>
      </template>
      <el-table :data="orderHistory" stripe>
        <el-table-column prop="orderId" label="订单号" width="180" />
        <el-table-column prop="description" label="商品描述" />
        <el-table-column prop="amount" label="金额" width="100">
          <template #default="{ row }">
            ￥{{ (row.amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="payType" label="支付方式" width="100">
          <template #default="{ row }">
            {{ row.payType === 'native' ? '扫码' : 'JSAPI' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              link
              @click="queryOrderStatus(row.orderId)"
            >
              查询状态
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 支付弹窗 -->
    <WechatPayModal
      v-model="payModalVisible"
      title="支付"
      :description="currentOrder.description"
      :amount="currentOrder.amount"
      :order-id="currentOrder.orderId"
      :pay-type="orderForm.payType"
      :openid="orderForm.openid"
      :attach="orderForm.attach"
      @success="handlePaySuccess"
      @failed="handlePayFailed"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getWechatPayConfig, queryWechatOrder } from '@/api/wechatPay'
import WechatPayModal from '@/components/WechatPayModal.vue'

// 支付配置
const payConfig = ref({
  mch_id: '',
  app_id: '',
  jsapi_available: false,
  notify_url: '',
  pay_timeout: 900
})

// 订单表单
const formRef = ref(null)
const creating = ref(false)
const orderForm = reactive({
  description: '测试商品-微信支付',
  amountYuan: 1.00,
  payType: 'native',
  openid: '',
  attach: ''
})

const formRules = {
  description: [
    { required: true, message: '请输入商品描述', trigger: 'blur' }
  ],
  amountYuan: [
    { required: true, message: '请输入支付金额', trigger: 'blur' }
  ]
}

// 支付弹窗
const payModalVisible = ref(false)
const currentOrder = reactive({
  description: '',
  amount: 0,
  orderId: ''
})

// 订单历史
const orderHistory = ref([])

// 加载支付配置
const loadPayConfig = async () => {
  try {
    const res = await getWechatPayConfig()
    payConfig.value = res
  } catch (error) {
    console.error('加载支付配置失败:', error)
    ElMessage.error('加载支付配置失败')
  }
}

// 创建订单
const handleCreateOrder = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  if (orderForm.payType === 'jsapi' && !orderForm.openid) {
    ElMessage.warning('JSAPI支付需要提供用户OpenID')
    return
  }

  creating.value = true
  
  try {
    currentOrder.description = orderForm.description
    currentOrder.amount = Math.round(orderForm.amountYuan * 100)
    currentOrder.orderId = ''
    
    // 打开支付弹窗
    payModalVisible.value = true
  } finally {
    creating.value = false
  }
}

// 支付成功
const handlePaySuccess = (data) => {
  console.log('支付成功:', data)
  ElMessage.success('支付成功！')
  
  // 添加到历史
  orderHistory.value.unshift({
    orderId: data.orderId,
    description: currentOrder.description,
    amount: currentOrder.amount,
    payType: orderForm.payType,
    status: 'SUCCESS',
    transactionId: data.transactionId
  })
}

// 支付失败
const handlePayFailed = (data) => {
  console.log('支付失败:', data)
  ElMessage.error(data.reason || '支付失败')
  
  // 添加到历史
  orderHistory.value.unshift({
    orderId: data.orderId,
    description: currentOrder.description,
    amount: currentOrder.amount,
    payType: orderForm.payType,
    status: 'FAILED'
  })
}

// 查询订单状态
const queryOrderStatus = async (orderId) => {
  try {
    const res = await queryWechatOrder(orderId)
    if (res.success) {
      ElMessage.success(`订单状态: ${res.trade_state_text}`)
      
      // 更新历史记录中的状态
      const order = orderHistory.value.find(o => o.orderId === orderId)
      if (order) {
        order.status = res.trade_state
      }
    } else {
      ElMessage.error(res.message || '查询失败')
    }
  } catch (error) {
    console.error('查询订单状态失败:', error)
    ElMessage.error('查询订单状态失败')
  }
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    'SUCCESS': 'success',
    'PAYERROR': 'danger',
    'CLOSED': 'info',
    'NOTPAY': 'warning'
  }
  return typeMap[status] || 'info'
}

// 页面加载时获取配置
onMounted(() => {
  loadPayConfig()
})
</script>

<style scoped>
.pay-demo-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.pay-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-info {
  margin-bottom: 20px;
}

.config-info h4 {
  margin-bottom: 12px;
  color: #303133;
}

.amount-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.orders-card {
  margin-top: 20px;
}
</style>
