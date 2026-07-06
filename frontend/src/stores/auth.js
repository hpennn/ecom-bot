/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authApi from '@/api/auth'
import paymentApi from '@/api/payment'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const paymentStatus = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')
  const isPaid = computed(() => paymentStatus.value?.paid ?? true)
  const isAdmin = computed(() => paymentStatus.value?.is_admin ?? false)
  const paidType = computed(() => paymentStatus.value?.paid_type || 'free')

  async function login(form) {
    const res = await authApi.login(form)
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    // 登录后获取付费状态
    await fetchPaymentStatus()
    router.push('/')
  }

  async function register(form) {
    const res = await authApi.register(form)
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    await fetchPaymentStatus()
    router.push('/')
  }

  async function fetchPaymentStatus() {
    if (!token.value) return
    try {
      const res = await paymentApi.getStatus()
      paymentStatus.value = res
    } catch (e) {
      console.error('获取付费状态失败', e)
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    paymentStatus.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  return {
    token, user, paymentStatus,
    isLoggedIn, username, isPaid, isAdmin, paidType,
    login, register, logout, fetchPaymentStatus
  }
})
