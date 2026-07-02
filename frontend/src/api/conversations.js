/**
 * 对话管理 API
 */
import api from '@/utils/request'

export default {
  getList: (storeId, params) => api.get(`/stores/${storeId}/conversations`, { params }),
  getMessages: (convId) => api.get(`/conversations/${convId}/messages`),
  reply: (convId, content) => api.post(`/conversations/${convId}/reply`, { content }),
  transfer: (convId) => api.post(`/conversations/${convId}/transfer`),
  close: (convId) => api.post(`/conversations/${convId}/close`),
  stats: (storeId) => api.get(`/stores/${storeId}/stats`)
}
