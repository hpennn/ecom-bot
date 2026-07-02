<template>
  <el-container class="main-layout">
    <!-- 左侧菜单栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo">
        <el-icon v-if="isCollapse"><Shop /></el-icon>
        <span v-else>电商客服机器人</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        class="sidebar-menu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/stores">
          <el-icon><Shop /></el-icon>
          <template #title>店铺管理</template>
        </el-menu-item>
        
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
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
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-button 
            :icon="isCollapse ? 'Expand' : 'Fold'" 
            text 
            @click="isCollapse = !isCollapse"
          />
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentStore">{{ currentStore.name }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 当前店铺选择 -->
          <el-select 
            v-if="stores.length > 0" 
            v-model="selectedStoreId" 
            placeholder="选择店铺"
            class="store-selector"
            @change="handleStoreChange"
          >
            <el-option
              v-for="store in stores"
              :key="store.id"
              :label="store.name"
              :value="store.id"
            />
          </el-select>
          
          <!-- 用户菜单 -->
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
        <div class="footer-icp">
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">粤ICP备2026087091号-1</a>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useStoreStore } from '@/stores/store'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const storeStore = useStoreStore()

// 折叠状态
const isCollapse = ref(false)

// 计算属性
const username = computed(() => authStore.username)
const stores = computed(() => storeStore.stores)
const currentStore = computed(() => storeStore.currentStore)

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 选中的店铺ID
const selectedStoreId = computed({
  get: () => storeStore.currentStoreId || '',
  set: (val) => {
    const store = stores.value.find(s => s.id === val)
    if (store) storeStore.setCurrentStore(store)
  }
})

// 处理用户菜单命令
const handleUserCommand = (command) => {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
  }
}

// 处理店铺切换
const handleStoreChange = (storeId) => {
  const store = stores.value.find(s => s.id === storeId)
  if (store) {
    storeStore.setCurrentStore(store)
    ElMessage.success(`已切换到 ${store.name}`)
  }
}

// 初始化
onMounted(async () => {
  // 获取店铺列表
  await storeStore.fetchStores()
  storeStore.restoreCurrentStore()
  
  // 如果没有当前店铺但有店铺列表，自动选择第一个
  if (!currentStore.value && stores.value.length > 0) {
    storeStore.setCurrentStore(stores.value[0])
  }
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.aside {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background: #263445;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.logo .el-icon {
  font-size: 24px;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
}

.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-menu-item.is-active {
  background: #263445 !important;
  color: #409eff;
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.store-selector {
  width: 160px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #606266;
}

.user-info:hover {
  color: #409eff;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.footer-icp {
  text-align: center;
  padding: 16px 0 8px;
  font-size: 12px;
  color: #999;
}

.footer-icp a {
  color: #999;
  text-decoration: none;
}

.footer-icp a:hover {
  color: #409eff;
}
</style>
