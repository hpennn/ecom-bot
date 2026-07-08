/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/payment',
    name: 'Payment',
    component: () => import('@/views/Payment.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'stores',
        name: 'Stores',
        component: () => import('@/views/Stores.vue'),
        meta: { title: '店铺管理' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue'),
        meta: { title: '知识库' }
      },
      {
        path: 'conversations',
        name: 'Conversations',
        component: () => import('@/views/Conversations.vue'),
        meta: { title: '对话记录' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置' }
      },
      {
        path: 'keyword-replies',
        name: 'KeywordReplies',
        component: () => import('@/views/KeywordReplies.vue'),
        meta: { title: '关键词回复' }
      },
      {
        path: 'transfer-keywords',
        name: 'TransferKeywords',
        component: () => import('@/views/TransferKeywords.vue'),
        meta: { title: '转人工配置' }
      },
      {
        path: 'sensitive-words',
        name: 'SensitiveWords',
        component: () => import('@/views/SensitiveWords.vue'),
        meta: { title: '敏感词管理' }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { title: '数据统计' }
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/Admin.vue'),
        meta: { title: '管理后台', requiresAdmin: true }
      },
      {
        path: 'pay-demo',
        name: 'PayDemo',
        component: () => import('@/pages/PayDemo.vue'),
        meta: { title: '支付测试' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next('/')
  } else {
    next()
  }
})

export default router
