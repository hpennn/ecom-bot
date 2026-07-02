<template>
  <div class="store-create-page">
    <div class="page-card">
      <div class="page-header">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2>创建店铺</h2>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="store-form"
      >
        <el-form-item label="店铺名称" prop="name">
          <el-input 
            v-model="form.name" 
            placeholder="请输入店铺名称，如：我的拼多多店"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="平台" prop="platform">
          <el-radio-group v-model="form.platform">
            <el-radio label="pinduoduo">
              <span class="platform-option">
                <span>拼多多</span>
                <span class="platform-desc">支持拼多多电商平台</span>
              </span>
            </el-radio>
            <el-radio label="taobao">
              <span class="platform-option">
                <span>淘宝</span>
                <span class="platform-desc">支持淘宝/天猫平台</span>
              </span>
            </el-radio>
            <el-radio label="jd">
              <span class="platform-option">
                <span>京东</span>
                <span class="platform-desc">支持京东电商平台</span>
              </span>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-switch
            v-model="form.status"
            active-value="active"
            inactive-value="inactive"
            active-text="运行中"
            inactive-text="已停用"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            创建店铺
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStoreStore } from '@/stores/store'
import { ElMessage } from 'element-plus'

const router = useRouter()
const storeStore = useStoreStore()

const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  name: '',
  platform: 'pinduoduo',
  status: 'active'
})

const rules = {
  name: [
    { required: true, message: '请输入店铺名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  platform: [
    { required: true, message: '请选择平台', trigger: 'change' }
  ]
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const newStore = await storeStore.createStoreAction(form)
    ElMessage.success('店铺创建成功')
    router.push(`/stores/${newStore.id}`)
  } catch (error) {
    // 错误已由 axios 拦截器处理
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.store-create-page {
  max-width: 600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 20px;
  color: #303133;
  margin: 0;
}

.store-form {
  max-width: 500px;
}

.platform-option {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.platform-desc {
  font-size: 12px;
  color: #909399;
}
</style>
