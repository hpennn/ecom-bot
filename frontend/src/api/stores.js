/**
 * 店铺管理 API
 */
import api from '@/utils/request'

export default {
  getList: () => api.get('/stores'),
  get: (id) => api.get(`/stores/${id}`),
  create: (data) => api.post('/stores', data),
  update: (id, data) => api.put(`/stores/${id}`, data),
  remove: (id) => api.delete(`/stores/${id}`),
  stats: (id) => api.get(`/stores/${id}/stats`)
}
