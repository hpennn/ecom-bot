/**
 * 知识库管理 API
 */
import api from '@/utils/request'

export default {
  getList: (storeId) => api.get(`/stores/${storeId}/knowledge`),
  create: (storeId, data) => api.post(`/stores/${storeId}/knowledge`, data),
  update: (id, data) => api.put(`/knowledge/${id}`, data),
  remove: (id) => api.delete(`/knowledge/${id}`),
  batchImport: (storeId, formData) => api.post(`/stores/${storeId}/knowledge/batch`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  testReply: (storeId, question) => api.post(`/stores/${storeId}/reply`, { message: question })
}
