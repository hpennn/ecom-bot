<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="420px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 支付方式选择 -->
    <div v-if="step === 'select'" class="pay-methods">
      <div class="pay-method-item" @click="selectPayMethod('wechat')">
        <img src="@/assets/wechat-pay-logo.png" class="pay-logo" @error="handleLogoError" />
        <span>微信支付</span>
        <el-icon class="check-icon"><Check v-if="selectedMethod === 'wechat'" /></el-icon>
      </div>
      <div class="pay-method-item" @click="selectPayMethod('alipay')">
        <img src="@/assets/alipay-logo.png" class="pay-logo" @error="handleLogoError" />
        <span>支付宝</span>
        <el-tag size="small" type="info">虎皮椒</el-tag>
        <el-icon class="check-icon"><Check v-if="selectedMethod === 'alipay'" /></el-icon>
      </div>
    </div>

    <!-- 微信支付内容 -->
    <div v-else-if="step === 'wechat' && payType === 'native'" class="wechat-pay-content">
      <div class="qrcode-container">
        <div v-if="qrcodeUrl" class="qrcode-wrapper">
          <img :src="qrcodeUrl" alt="微信支付二维码" class="qrcode-img" />
        </div>
        <div v-else class="qrcode-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在生成二维码...</span>
        </div>
      </div>
      <div class="pay-tip">
        <p>请使用微信扫码支付</p>
        <p class="amount">￥{{ (amount / 100).toFixed(2) }}</p>
      </div>
    </div>

    <!-- JSAPI支付内容 -->
    <div v-else-if="step === 'wechat' && payType === 'jsapi'" class="jsapi-pay-content">
      <div v-if="jsapiReady" class="jsapi-tip">
        <el-icon size="48" color="#07C160"><Promotion /></el-icon>
        <p>即将调起微信支付</p>
        <p class="amount">￥{{ (amount / 100).toFixed(2) }}</p>
      </div>
      <div v-else class="jsapi-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>准备支付...</span>
      </div>
    </div>

    <!-- 支付宝支付内容 -->
    <div v-else-if="step === 'alipay'" class="alipay-content">
      <div class="alipay-tip">
        <el-icon size="48" color="#1677FF"><Money /></el-icon>
        <p>支付宝支付</p>
        <p class="amount">￥{{ (amount / 100).toFixed(2) }}</p>
        <p class="alipay-note">即将跳转到支付宝...</p>
      </div>
    </div>

    <!-- 支付状态 -->
    <div v-else-if="step === 'status'" class="pay-status">
      <div v-if="payStatus === 'success'" class="status-success">
        <el-icon size="64" color="#67C23A"><CircleCheck /></el-icon>
        <h3>支付成功</h3>
        <p>感谢您的支持</p>
      </div>
      <div v-else-if="payStatus === 'failed'" class="status-failed">
        <el-icon size="64" color="#F56C6C"><CircleClose /></el-icon>
        <h3>支付失败</h3>
        <p>{{ failReason || '请稍后重试' }}</p>
      </div>
      <div v-else class="status-pending">
        <el-icon class="is-loading" size="48"><Loading /></el-icon>
        <h3>等待支付</h3>
        <p>请确认是否已完成支付</p>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button v-if="step === 'select'" @click="handleClose">取消</el-button>
        <el-button v-else-if="step === 'wechat' || step === 'alipay'" @click="goBack">
          返回选择
        </el-button>
        <el-button v-if="step === 'status' && payStatus !== 'success'" type="primary" @click="retryPay">
          重新支付
        </el-button>
        <el-button v-if="step === 'status'" type="success" @click="handleSuccess">
          完成
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Loading, Promotion, Money, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { createWechatOrder, queryWechatOrder, getPayQrcode } from '@/api/wechatPay'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '选择支付方式'
  },
  description: {
    type: String,
    default: '商品支付'
  },
  amount: {
    type: Number,
    required: true
  },
  orderId: {
    type: String,
    default: ''
  },
  payType: {
    type: String,
    default: 'native' // native: 扫码支付, jsapi: JSAPI支付
  },
  openid: {
    type: String,
    default: ''
  },
  attach: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'failed', 'close'])

// 弹窗控制
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const dialogTitle = computed(() => {
  if (step.value === 'status') {
    if (payStatus.value === 'success') return '支付成功'
    if (payStatus.value === 'failed') return '支付失败'
    return '支付处理中'
  }
  return props.title
})

// 步骤控制: select -> wechat/alipay -> status
const step = ref('select')
const selectedMethod = ref('')
const payStatus = ref('')
const failReason = ref('')

// 微信支付相关
const currentOrderId = ref('')
const qrcodeUrl = ref('')
const jsapiReady = ref(false)
const pollTimer = ref(null)

// 选择支付方式
const selectPayMethod = (method) => {
  selectedMethod.value = method
  if (method === 'wechat') {
    step.value = 'wechat'
    initWechatPay()
  } else if (method === 'alipay') {
    step.value = 'alipay'
    handleAlipay()
  }
}

// 初始化微信支付
const initWechatPay = async () => {
  if (props.payType === 'native') {
    await createNativeOrder()
  } else {
    await createJsapiOrder()
  }
}

// Native支付 - 创建扫码订单
const createNativeOrder = async () => {
  try {
    const res = await createWechatOrder({
      description: props.description,
      amount: props.amount,
      pay_type: 'native',
      attach: props.attach,
      order_id: props.orderId || undefined
    })

    if (res.success) {
      currentOrderId.value = res.order_id
      if (res.qr_code_url) {
        qrcodeUrl.value = res.qr_code_url
      } else if (res.code_url) {
        // 如果后端直接返回code_url，需要前端生成二维码
        qrcodeUrl.value = getPayQrcode(currentOrderId.value)
      }
      startPollStatus()
    } else {
      ElMessage.error(res.message || '创建订单失败')
      step.value = 'status'
      payStatus.value = 'failed'
      failReason.value = res.message
    }
  } catch (error) {
    console.error('创建微信支付订单失败:', error)
    ElMessage.error('创建订单失败，请稍后重试')
    step.value = 'status'
    payStatus.value = 'failed'
    failReason.value = error.message || '网络错误'
  }
}

// JSAPI支付 - 创建调起支付
const createJsapiOrder = async () => {
  if (!props.openid) {
    ElMessage.warning('JSAPI支付需要用户授权')
    step.value = 'status'
    payStatus.value = 'failed'
    failReason.value = '缺少用户openid'
    return
  }

  try {
    const res = await createWechatOrder({
      description: props.description,
      amount: props.amount,
      pay_type: 'jsapi',
      openid: props.openid,
      attach: props.attach,
      order_id: props.orderId || undefined
    })

    if (res.success) {
      currentOrderId.value = res.order_id
      const paymentParams = res.payment_params
      
      // 调起微信支付
      if (typeof window.WeixinJSBridge !== 'undefined') {
        window.WeixinJSBridge.invoke(
          'getBrandWCPayRequest',
          {
            appId: paymentParams.appId,
            timeStamp: paymentParams.timeStamp,
            nonceStr: paymentParams.nonceStr,
            package: paymentParams.package,
            signType: paymentParams.signType,
            paySign: paymentParams.paySign
          },
          (res) => {
            if (res.err_msg === 'get_brand_wcpay_request:ok') {
              payStatus.value = 'success'
              step.value = 'status'
              stopPollStatus()
              emit('success', { orderId: currentOrderId.value })
            } else if (res.err_msg === 'get_brand_wcpay_request:cancel') {
              payStatus.value = 'failed'
              failReason.value = '用户取消支付'
              step.value = 'status'
            } else {
              payStatus.value = 'failed'
              failReason.value = res.err_desc || res.err_msg || '支付失败'
              step.value = 'status'
            }
          }
        )
      } else {
        // 微信内置浏览器外，需要提示
        ElMessage.info('请在微信内完成支付')
        jsapiReady.value = true
        // 启动轮询
        startPollStatus()
      }
    } else if (res.code === 'APPID_NOT_CONFIGURED') {
      ElMessage.warning(res.message || 'JSAPI支付暂不可用')
      step.value = 'status'
      payStatus.value = 'failed'
      failReason.value = '公众号AppID尚未配置'
    } else {
      ElMessage.error(res.message || '创建订单失败')
      step.value = 'status'
      payStatus.value = 'failed'
      failReason.value = res.message
    }
  } catch (error) {
    console.error('创建JSAPI支付订单失败:', error)
    ElMessage.error('创建订单失败，请稍后重试')
    step.value = 'status'
    payStatus.value = 'failed'
    failReason.value = error.message || '网络错误'
  }
}

// 轮询查询订单状态
const startPollStatus = () => {
  stopPollStatus()
  pollTimer.value = setInterval(async () => {
    if (!currentOrderId.value || step.value === 'status') {
      stopPollStatus()
      return
    }
    
    try {
      const res = await queryWechatOrder(currentOrderId.value)
      if (res.success) {
        const state = res.trade_state
        if (state === 'SUCCESS') {
          payStatus.value = 'success'
          step.value = 'status'
          stopPollStatus()
          emit('success', { 
            orderId: currentOrderId.value,
            transactionId: res.transaction_id 
          })
        } else if (state === 'PAYERROR' || state === 'CLOSED') {
          payStatus.value = 'failed'
          failReason.value = res.trade_state_text
          step.value = 'status'
          stopPollStatus()
          emit('failed', { 
            orderId: currentOrderId.value,
            reason: res.trade_state_text 
          })
        }
        // NOTPAY 继续轮询
      }
    } catch (error) {
      console.error('查询订单状态失败:', error)
    }
  }, 3000)
}

const stopPollStatus = () => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

// 支付宝支付（虎皮椒）
const handleAlipay = () => {
  // TODO: 调用虎皮椒支付宝接口
  ElMessage.info('支付宝支付功能开发中')
}

// 返回选择支付方式
const goBack = () => {
  stopPollStatus()
  step.value = 'select'
  selectedMethod.value = ''
  qrcodeUrl.value = ''
  jsapiReady.value = false
}

// 重新支付
const retryPay = () => {
  step.value = 'select'
  payStatus.value = ''
  failReason.value = ''
  qrcodeUrl.value = ''
}

// 支付成功
const handleSuccess = () => {
  handleClose()
}

// 关闭弹窗
const handleClose = () => {
  stopPollStatus()
  dialogVisible.value = false
  emit('close')
}

// 处理Logo加载失败
const handleLogoError = (e) => {
  e.target.style.display = 'none'
}

// 监听弹窗关闭
watch(dialogVisible, (val) => {
  if (!val) {
    stopPollStatus()
    step.value = 'select'
    selectedMethod.value = ''
    payStatus.value = ''
    failReason.value = ''
    qrcodeUrl.value = ''
  }
})

// 组件卸载时清理
onUnmounted(() => {
  stopPollStatus()
})
</script>

<style scoped>
.pay-methods {
  padding: 8px 0;
}

.pay-method-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.pay-method-item:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.pay-logo {
  width: 32px;
  height: 32px;
  margin-right: 12px;
}

.pay-method-item span {
  flex: 1;
  font-size: 16px;
  color: #303133;
}

.check-icon {
  color: #409eff;
  font-size: 20px;
}

.qrcode-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.qrcode-wrapper {
  padding: 16px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
}

.qrcode-img {
  width: 200px;
  height: 200px;
}

.qrcode-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: #909399;
}

.pay-tip {
  text-align: center;
  margin-top: 16px;
}

.pay-tip p {
  margin: 4px 0;
  color: #606266;
}

.pay-tip .amount {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.jsapi-pay-content,
.alipay-content,
.pay-status {
  padding: 20px 0;
  text-align: center;
}

.jsapi-tip,
.alipay-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.jsapi-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 0;
  color: #909399;
}

.alipay-note {
  color: #909399;
  font-size: 14px;
}

.status-success,
.status-failed,
.status-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.status-success h3,
.status-failed h3,
.status-pending h3 {
  margin: 8px 0;
  font-size: 20px;
  color: #303133;
}

.status-success p,
.status-failed p,
.status-pending p {
  margin: 4px 0;
  color: #606266;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
