<template>
  <div class="conversation-detail-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <el-button text @click="$router.push('/conversations')">
        <el-icon><ArrowLeft /></el-icon>
        返回对话列表
      </el-button>
      <div class="header-info" v-if="conversation">
        <span>与 <strong>{{ conversation.customer }}</strong> 的对话</span>
        <el-tag :type="conversation.status === 'active' ? 'success' : 'info'">
          {{ conversation.status === 'active' ? '进行中' : '已关闭' }}
        </el-tag>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="conversation-container page-card" v-loading="loading">
      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <div v-if="messages.length === 0" class="empty-messages">
          <el-icon><ChatLineRound /></el-icon>
          <p>暂无消息记录</p>
        </div>
        
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-item"
          :class="msg.type"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.type === 'customer'"><User /></el-icon>
            <el-icon v-else-if="msg.type === 'bot'"><Cpu /></el-icon>
            <el-icon v-else><Service /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              {{ msg.content }}
            </div>
            <div class="message-time">{{ formatTime(msg.createdAt) }}</div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="message-input" v-if="conversation?.status === 'active'">
        <el-input
          v-model="replyContent"
          type="textarea"
          :rows="3"
          placeholder="输入回复内容..."
          resize="none"
          @keydown.enter.ctrl="handleSendReply"
        />
        <div class="input-actions">
          <el-button @click="handleClose">
            关闭对话
          </el-button>
          <el-button type="primary" :loading="sending" @click="handleSendReply">
            发送回复
            <span class="shortcut-hint">(Ctrl+Enter)</span>
          </el-button>
        </div>
      </div>
      
      <div v-else class="conversation-closed">
        <el-tag type="info" size="large">此对话已关闭</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStoreStore } from '@/stores/store'
import { getMessages, sendManualReply, closeConversation } from '@/api/conversations'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const storeStore = useStoreStore()

const loading = ref(false)
const sending = ref(false)
const messages = ref([])
const conversation = ref(null)
const replyContent = ref('')
const messageListRef = ref(null)

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 加载对话详情
const loadConversationDetail = async () => {
  const id = route.params.id
  loading.value = true
  
  try {
    const res = await getMessages(id)
    messages.value = res.messages || res || []
    
    // 模拟对话信息
    conversation.value = {
      id: parseInt(id),
      customer: '用户_' + id,
      status: parseInt(id) % 3 === 0 ? 'closed' : 'active'
    }
    
    scrollToBottom()
  } catch (error) {
    console.error('加载对话详情失败:', error)
    // 使用模拟数据
    messages.value = generateMockMessages()
    conversation.value = {
      id: parseInt(id),
      customer: '用户_' + id,
      status: parseInt(id) % 3 === 0 ? 'closed' : 'active'
    }
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

// 生成模拟消息
const generateMockMessages = () => {
  return [
    { id: 1, type: 'customer', content: '你好，我想问一下这款商品有没有优惠？', createdAt: new Date(Date.now() - 600000).toISOString() },
    { id: 2, type: 'bot', content: '您好！感谢您的咨询。这款商品目前正在参与满减活动，满200减30，全场包邮。', createdAt: new Date(Date.now() - 580000).toISOString() },
    { id: 3, type: 'customer', content: '那发货时间是什么时候呢？', createdAt: new Date(Date.now() - 560000).toISOString() },
    { id: 4, type: 'bot', content: '下单后48小时内发货，全国大部分地区预计3-5天送达。', createdAt: new Date(Date.now() - 540000).toISOString() },
    { id: 5, type: 'customer', content: '好的，那我下单了，谢谢！', createdAt: new Date(Date.now() - 300000).toISOString() }
  ]
}

// 发送回复
const handleSendReply = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  
  sending.value = true
  try {
    await sendManualReply(conversation.value.id, replyContent.value)
    
    // 添加消息到列表
    messages.value.push({
      id: Date.now(),
      type: 'agent',
      content: replyContent.value,
      createdAt: new Date().toISOString()
    })
    
    replyContent.value = ''
    scrollToBottom()
    ElMessage.success('回复已发送')
  } catch (error) {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

// 关闭对话
const handleClose = async () => {
  try {
    await closeConversation(conversation.value.id)
    conversation.value.status = 'closed'
    ElMessage.success('对话已关闭')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 监听路由变化
watch(() => route.params.id, () => {
  if (route.params.id) {
    loadConversationDetail()
  }
})

onMounted(() => {
  loadConversationDetail()
})
</script>

<style scoped>
.conversation-detail-page {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #606266;
}

.conversation-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-messages {
  text-align: center;
  padding: 60px;
  color: #909399;
}

.empty-messages .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.customer {
  flex-direction: row;
}

.message-item.bot,
.message-item.agent {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-item.bot .message-avatar {
  background: #409eff;
  color: #fff;
}

.message-item.agent .message-avatar {
  background: #67c23a;
  color: #fff;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  word-break: break-word;
}

.message-item.customer .message-bubble {
  background: #ecf5ff;
  color: #303133;
}

.message-item.bot .message-bubble {
  background: #409eff;
  color: #fff;
}

.message-item.agent .message-bubble {
  background: #f4f4f5;
  color: #303133;
}

.message-time {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 4px;
}

.message-item.bot .message-time,
.message-item.agent .message-time {
  text-align: right;
}

.message-input {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

.shortcut-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.conversation-closed {
  padding: 20px;
  text-align: center;
  border-top: 1px solid #f0f0f0;
}
</style>
