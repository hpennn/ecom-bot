<template>
  <div class="conversations-page">
    <h2>对话记录</h2>

    <el-row :gutter="20">
      <!-- 对话列表 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>对话列表</span>
              <el-radio-group v-model="statusFilter" size="small" @change="loadConversations">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="active">进行中</el-radio-button>
                <el-radio-button label="closed">已关闭</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div v-loading="loading" class="conv-list">
            <div
              v-for="conv in conversations"
              :key="conv.id"
              class="conv-item"
              :class="{ active: selectedConv?.id === conv.id }"
              @click="selectConv(conv)"
            >
              <div class="conv-name">{{ conv.customer_name || '匿名客户' }}</div>
              <div class="conv-preview">{{ conv.last_message || '暂无消息' }}</div>
              <div class="conv-meta">
                <el-tag :type="conv.status === 'active' ? 'success' : 'info'" size="small">
                  {{ conv.status === 'active' ? '进行中' : '已关闭' }}
                </el-tag>
                <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
              </div>
            </div>
            <el-empty v-if="!conversations.length && !loading" description="暂无对话" :image-size="60" />
          </div>
        </el-card>
      </el-col>

      <!-- 消息详情 -->
      <el-col :span="14">
        <el-card style="height: 100%">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center" v-if="selectedConv">
              <span>{{ selectedConv.customer_name || '匿名客户' }} - 对话详情</span>
              <div>
                <el-button v-if="selectedConv.status === 'active'" type="warning" size="small" @click="transferConv">转人工</el-button>
                <el-button v-if="selectedConv.status === 'active'" type="danger" size="small" @click="closeConv">关闭对话</el-button>
              </div>
            </div>
            <span v-else>请选择一个对话</span>
          </template>

          <div class="messages-area" v-if="selectedConv" v-loading="loadingMessages">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="message"
              :class="'msg-' + msg.role"
            >
              <div class="msg-sender">{{ { customer: '客户', bot: 'AI机器人', human: '人工客服' }[msg.role] || msg.role }}</div>
              <div class="msg-content">{{ msg.content }}</div>
              <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
            </div>
            <el-empty v-if="!messages.length && !loadingMessages" description="暂无消息" :image-size="60" />
          </div>
          <el-empty v-else description="请从左侧选择一个对话查看详情" :image-size="80" />

          <!-- 手动回复 -->
          <div v-if="selectedConv && selectedConv.status === 'active'" class="reply-area">
            <el-input v-model="replyText" placeholder="输入手动回复内容..." @keyup.enter="sendReply">
              <template #append>
                <el-button @click="sendReply" :loading="sending">发送</el-button>
              </template>
            </el-input>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import api from '@/utils/request'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const conversations = ref([])
const messages = ref([])
const selectedConv = ref(null)
const statusFilter = ref('')
const loading = ref(false)
const loadingMessages = ref(false)
const replyText = ref('')
const sending = ref(false)

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadConversations() {
  if (!appStore.currentStoreId) return
  loading.value = true
  try {
    let url = `/api/stores/${appStore.currentStoreId}/conversations`
    if (statusFilter.value) url += `?status=${statusFilter.value}`
    const data = await api.get(url)
    conversations.value = data || []
  } catch (e) {
    conversations.value = []
  } finally {
    loading.value = false
  }
}

async function selectConv(conv) {
  selectedConv.value = conv
  loadingMessages.value = true
  try {
    const data = await api.get(`/conversations/${conv.id}/messages`)
    messages.value = data || []
  } catch (e) {
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

async function sendReply() {
  if (!replyText.value.trim()) return
  sending.value = true
  try {
    await api.post(`/conversations/${selectedConv.value.id}/reply`, { content: replyText.value })
    messages.value.push({ role: 'human', content: replyText.value, created_at: new Date().toISOString() })
    replyText.value = ''
    ElMessage.success('已发送')
  } catch (e) {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

async function transferConv() {
  try {
    await api.post(`/conversations/${selectedConv.value.id}/transfer`)
    ElMessage.success('已转人工')
    await selectConv(selectedConv.value)
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function closeConv() {
  try {
    await api.post(`/conversations/${selectedConv.value.id}/close`)
    selectedConv.value.status = 'closed'
    ElMessage.success('对话已关闭')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

import { watch } from 'vue'
watch(() => appStore.currentStoreId, loadConversations)
onMounted(loadConversations)
</script>

<style scoped>
.conv-list { max-height: 600px; overflow-y: auto; }
.conv-item { padding: 12px; border-bottom: 1px solid #f0f0f0; cursor: pointer; transition: background 0.2s; }
.conv-item:hover { background: #f5f7fa; }
.conv-item.active { background: #ecf5ff; }
.conv-name { font-weight: 600; margin-bottom: 4px; }
.conv-preview { color: #999; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.conv-time { font-size: 12px; color: #aaa; }
.messages-area { height: 450px; overflow-y: auto; padding: 16px 0; }
.message { margin-bottom: 16px; padding: 8px 12px; border-radius: 8px; max-width: 80%; }
.msg-customer { background: #f0f0f0; margin-right: auto; }
.msg-bot { background: #ecf5ff; margin-left: auto; }
.msg-human { background: #f0f9eb; margin-left: auto; }
.msg-sender { font-size: 12px; color: #999; margin-bottom: 4px; }
.msg-content { line-height: 1.5; }
.msg-time { font-size: 11px; color: #bbb; margin-top: 4px; text-align: right; }
.reply-area { margin-top: 16px; padding-top: 16px; border-top: 1px solid #eee; }
</style>
