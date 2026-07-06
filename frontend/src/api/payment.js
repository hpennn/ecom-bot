/**
 * 支付 API
 */
import api from '@/utils/request'

export default {
  // 查询付费状态
  getStatus: () => api.get('/payment/status'),
  // 获取价格信息
  getPrices: () => api.get('/payment/prices'),
  // 创建支付订单
  createPayment: (data) => api.post('/payment/create', data),
  // 检查订单状态
  checkOrder: (orderId) => api.get(`/payment/check/${orderId}`),
}
