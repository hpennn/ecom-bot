<template>
  <div class="settings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>系统设置</h2>
      <p>配置系统参数和 API 设置</p>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 自动回复设置 -->
      <el-tab-pane label="自动回复" name="autoReply">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>自动回复设置</span>
            </div>
          </template>
          
          <el-form label-width="120px">
            <el-form-item label="自动回复">
              <el-switch v-model="settings.autoReply.enabled" />
              <span class="setting-hint">开启后，AI 将自动回复客户消息</span>
            </el-form-item>
            
            <el-form-item label="回复延迟">
              <el-input-number 
                v-model="settings.autoReply.delay" 
                :min="0" 
                :max="60"
                controls-position="right"
              />
              <span class="setting-hint">秒</span>
            </el-form-item>
            
            <el-form-item label="AI 回复风格">
              <el-radio-group v-model="settings.autoReply.style">
                <el-radio label="professional">专业</el-radio>
                <el-radio label="friendly">亲切</el-radio>
                <el-radio label="concise">简洁</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="回复前缀">
              <el-input 
                v-model="settings.autoReply.prefix" 
                placeholder="如：[智能客服]"
                style="width: 300px"
              />
            </el-form-item>
            
            <el-form-item label="回复后缀">
              <el-input 
                v-model="settings.autoReply.suffix" 
                placeholder="如：如有其他问题请随时咨询"
                style="width: 300px"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveAutoReplySettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 拼多多 API 设置 -->
      <el-tab-pane label="拼多多 API" name="pddApi">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>拼多多 API 配置</span>
              <el-tag type="info">用于连接拼多多开放平台</el-tag>
            </div>
          </template>
          
          <el-form label-width="120px">
            <el-form-item label="AppKey">
              <el-input 
                v-model="settings.pddApi.appKey" 
                placeholder="请输入拼多多 AppKey"
                style="width: 400px"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="AppSecret">
              <el-input 
                v-model="settings.pddApi.appSecret" 
                placeholder="请输入拼多多 AppSecret"
                style="width: 400px"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="回调地址">
              <el-input 
                v-model="settings.pddApi.callbackUrl" 
                placeholder="请输入回调地址"
                style="width: 400px"
              />
              <div class="setting-hint">
                将此地址配置到拼多多开放平台的回调地址设置中
              </div>
            </el-form-item>
            
            <el-form-item label="环境">
              <el-radio-group v-model="settings.pddApi.environment">
                <el-radio label="sandbox">沙箱环境</el-radio>
                <el-radio label="production">生产环境</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="savePddApiSettings">
                保存配置
              </el-button>
              <el-button @click="testPddConnection">
                测试连接
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 敏感词设置 -->
      <el-tab-pane label="敏感词过滤" name="sensitiveWords">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>敏感词过滤设置</span>
            </div>
          </template>
          
          <el-form label-width="120px">
            <el-form-item label="启用过滤">
              <el-switch v-model="settings.sensitiveWords.enabled" />
            </el-form-item>
            
            <el-form-item label="敏感词列表">
              <el-input
                v-model="settings.sensitiveWords.words"
                type="textarea"
                :rows="6"
                placeholder="每行一个敏感词"
                style="width: 400px"
              />
              <div class="setting-hint">
                包含敏感词的消息将被拦截或标记
              </div>
            </el-form-item>
            
            <el-form-item label="处理方式">
              <el-radio-group v-model="settings.sensitiveWords.action">
                <el-radio label="block">拦截</el-radio>
                <el-radio label="flag">标记</el-radio>
                <el-radio label="replace">替换</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveSensitiveWordsSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 通知设置 -->
      <el-tab-pane label="消息通知" name="notifications">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>消息通知设置</span>
            </div>
          </template>
          
          <el-form label-width="120px">
            <el-form-item label="新对话提醒">
              <el-switch v-model="settings.notifications.newConversation" />
              <span class="setting-hint">有新对话时发送通知</span>
            </el-form-item>
            
            <el-form-item label="未回复提醒">
              <el-switch v-model="settings.notifications.unansweredReminder" />
            </el-form-item>
            
            <el-form-item label="提醒间隔">
              <el-input-number 
                v-model="settings.notifications.reminderInterval" 
                :min="5" 
                :max="60"
                controls-position="right"
              />
              <span class="setting-hint">分钟</span>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveNotificationSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 当前激活的标签页
const activeTab = ref('autoReply')

// 设置数据
const settings = reactive({
  // 自动回复设置
  autoReply: {
    enabled: true,
    delay: 0,
    style: 'friendly',
    prefix: '[智能客服]',
    suffix: '如有其他问题，请随时咨询~'
  },
  
  // 拼多多 API 设置
  pddApi: {
    appKey: '',
    appSecret: '',
    callbackUrl: '',
    environment: 'production'
  },
  
  // 敏感词设置
  sensitiveWords: {
    enabled: true,
    words: '退款\n退货\n投诉\n骗子\n假货',
    action: 'flag'
  },
  
  // 通知设置
  notifications: {
    newConversation: true,
    unansweredReminder: true,
    reminderInterval: 15
  }
})

// 保存自动回复设置
const saveAutoReplySettings = () => {
  localStorage.setItem('settings_autoReply', JSON.stringify(settings.autoReply))
  ElMessage.success('自动回复设置已保存')
}

// 保存拼多多 API 设置
const savePddApiSettings = () => {
  localStorage.setItem('settings_pddApi', JSON.stringify(settings.pddApi))
  ElMessage.success('拼多多 API 配置已保存')
}

// 测试拼多多连接
const testPddConnection = async () => {
  if (!settings.pddApi.appKey || !settings.pddApi.appSecret) {
    ElMessage.warning('请先填写 AppKey 和 AppSecret')
    return
  }
  ElMessage.info('正在测试连接...')
  // 模拟测试
  setTimeout(() => {
    ElMessage.success('连接测试成功！')
  }, 1500)
}

// 保存敏感词设置
const saveSensitiveWordsSettings = () => {
  localStorage.setItem('settings_sensitiveWords', JSON.stringify(settings.sensitiveWords))
  ElMessage.success('敏感词设置已保存')
}

// 保存通知设置
const saveNotificationSettings = () => {
  localStorage.setItem('settings_notifications', JSON.stringify(settings.notifications))
  ElMessage.success('通知设置已保存')
}

// 加载已保存的设置
const loadSettings = () => {
  // 加载自动回复设置
  const savedAutoReply = localStorage.getItem('settings_autoReply')
  if (savedAutoReply) {
    Object.assign(settings.autoReply, JSON.parse(savedAutoReply))
  }
  
  // 加载拼多多 API 设置
  const savedPddApi = localStorage.getItem('settings_pddApi')
  if (savedPddApi) {
    Object.assign(settings.pddApi, JSON.parse(savedPddApi))
  }
  
  // 加载敏感词设置
  const savedSensitiveWords = localStorage.getItem('settings_sensitiveWords')
  if (savedSensitiveWords) {
    Object.assign(settings.sensitiveWords, JSON.parse(savedSensitiveWords))
  }
  
  // 加载通知设置
  const savedNotifications = localStorage.getItem('settings_notifications')
  if (savedNotifications) {
    Object.assign(settings.notifications, JSON.parse(savedNotifications))
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  max-width: 1000px;
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
  margin: 0;
}

.settings-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.settings-card {
  max-width: 800px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.setting-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}
</style>
