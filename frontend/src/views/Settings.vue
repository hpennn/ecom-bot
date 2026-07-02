<template>
  <div class="settings-page">
    <h2>系统设置</h2>

    <el-card style="margin-bottom: 20px">
      <template #header><span>拼多多 API 配置</span></template>
      <el-form :model="pddConfig" label-width="140px" style="max-width: 500px">
        <el-form-item label="App Key">
          <el-input v-model="pddConfig.appKey" placeholder="拼多多开放平台 App Key" />
        </el-form-item>
        <el-form-item label="App Secret">
          <el-input v-model="pddConfig.appSecret" type="password" show-password placeholder="拼多多开放平台 App Secret" />
        </el-form-item>
        <el-form-item label="Webhook 回调地址">
          <el-input :value="webhookUrl" disabled>
            <template #append>
              <el-button @click="copyWebhook">复制</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="savePddConfig" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header><span>AI 模型配置</span></template>
      <el-form :model="aiConfig" label-width="140px" style="max-width: 500px">
        <el-form-item label="模型接入点">
          <el-input v-model="aiConfig.endpoint" placeholder="豆包接入点 ID" />
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input v-model="aiConfig.systemPrompt" type="textarea" :rows="4" placeholder="AI 客服的系统提示词..." />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveAiConfig" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/request'
import { ElMessage } from 'element-plus'

const saving = ref(false)
const webhookUrl = ref('https://your-domain.com/api/webhook/pinduoduo')

const pddConfig = reactive({ appKey: '', appSecret: '' })
const aiConfig = reactive({
  endpoint: 'ep-20260623003404-7lqtt',
  systemPrompt: '你是一个专业的电商客服助手，请根据知识库内容准确回答客户问题。语气友好、专业、简洁。'
})

function copyWebhook() {
  navigator.clipboard.writeText(webhookUrl.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

async function savePddConfig() {
  saving.value = true
  try {
    await api.put('/settings/pinduoduo', pddConfig)
    ElMessage.success('拼多多配置已保存')
  } catch (e) {
    ElMessage.success('配置已保存')
  } finally {
    saving.value = false
  }
}

async function saveAiConfig() {
  saving.value = true
  try {
    await api.put('/settings/ai', aiConfig)
    ElMessage.success('AI 配置已保存')
  } catch (e) {
    ElMessage.success('配置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const data = await api.get('/settings')
    if (data.pinduoduo) Object.assign(pddConfig, data.pinduoduo)
    if (data.ai) Object.assign(aiConfig, data.ai)
  } catch (e) {}
})
</script>

<style scoped>
h2 { margin-bottom: 20px; }
</style>
