/**
 * 管理后台 API
 */
import api from '@/utils/request'

// 管理后台请求需要带 x-admin-token
const adminApi = {
  getHeaders() {
    const token = localStorage.getItem('admin_token') || ''
    return token ? { 'x-admin-token': token } : {}
  },
  // 验证管理员
  verify: () => api.get('/admin/verify', { headers: adminApi.getHeaders() }),
  // 统计数据
  getStats: () => api.get('/admin/stats', { headers: adminApi.getHeaders() }),
  // 用户列表
  getUsers: () => api.get('/admin/users', { headers: adminApi.getHeaders() }),
  // 修改用户付费状态
  updateUser: (userId, data) => api.put(`/admin/users/${userId}`, data, { headers: adminApi.getHeaders() }),
  // 设置管理员
  setAdmin: (userId, data) => api.post(`/admin/users/${userId}/set-admin`, data, { headers: adminApi.getHeaders() }),
  // 订单列表
  getOrders: () => api.get('/admin/orders', { headers: adminApi.getHeaders() }),
  // 获取配置
  getConfig: () => api.get('/admin/config', { headers: adminApi.getHeaders() }),
}

export default adminApi
