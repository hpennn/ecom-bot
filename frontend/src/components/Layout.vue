<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <span v-if="!collapsed">🤖 电商客服机器人</span>
        <span v-else>🤖</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/stores">
          <el-icon><Shop /></el-icon>
          <template #title>店铺管理</template>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Reading /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>
        <el-menu-item index="/conversations">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>对话记录</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
        <el-menu-item v-if="authStore.isAdmin" index="/admin">
          <el-icon><Lock /></el-icon>
          <template #title>管理后台</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="appStore.toggleSidebar">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <!-- 店铺选择器 -->
          <el-select
            v-if="appStore.stores.length"
            v-model="appStore.currentStoreId"
            placeholder="选择店铺"
            size="small"
            style="width: 180px; margin-left: 16px"
            @change="appStore.setCurrentStore"
          >
            <el-option
              v-for="store in appStore.stores"
              :key="store.id"
              :label="store.name"
              :value="String(store.id)"
            />
          </el-select>
        </div>
        <div class="header-right">
          <!-- VIP 状态 -->
          <el-tag v-if="authStore.isPaid" type="success" effect="plain" round size="small">
            👑 {{ planLabel }}
          </el-tag>
          <el-button
            v-else
            type="warning"
            size="small"
            round
            @click="$router.push('/payment')"
          >
            💎 开通会员
          </el-button>
          <span class="username">{{ authStore.username }}</span>
          <el-button type="text" @click="authStore.logout">退出</el-button>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { DataBoard, Shop, Reading, ChatDotRound, Setting, Fold, Expand, Lock } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()
const collapsed = computed(() => appStore.sidebarCollapsed)

const planLabel = computed(() => {
  const type = authStore.paidType
  const labels = { monthly: '月度会员', yearly: '年度会员', permanent: '永久会员', free: '免费试用' }
  return labels[type] || type
})

onMounted(async () => {
  await authStore.fetchPaymentStatus()
  appStore.fetchStores()
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.sidebar {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #3a4a5e;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
  padding: 0 20px;
}
.header-left {
  display: flex;
  align-items: center;
}
.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #666;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  color: #666;
  font-size: 14px;
}
.main-content {
  background: #f5f7fa;
}
</style>
