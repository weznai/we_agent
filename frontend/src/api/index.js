import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

let isRedirecting = false

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.detail || error.message || '请求失败'
    const url = error.config?.url || ''

    if (status === 401 && !url.includes('/auth/')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!isRedirecting && router.currentRoute.value.path !== '/login') {
        isRedirecting = true
        router.push('/login').finally(() => { isRedirecting = false })
      }
    } else if (status === 400) {
      ElMessage.warning(msg)
    } else if (status !== 404) {
      ElMessage.error(msg)
    }

    return Promise.reject(error)
  }
)

export default api
