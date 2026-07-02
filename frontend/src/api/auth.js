/**
 * 认证 API
 */
import api from '@/utils/request'

export default {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me')
}
