import axios from 'axios'
import router from '../router'

// 创建Axios实例
const request = axios.create({
  baseURL: 'http://localhost:8000/api',  // 后端接口基础地址（FastAPI默认端口8000）
  timeout: 10000,
  // 不在全局强制 Content-Type；这样 JSON / 表单 / FormData 都能由 axios 自动处理
})

// 请求拦截器：添加JWT令牌
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 令牌过期，跳转至登录页
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      router.push('/login')
      if (typeof window !== 'undefined') {
        window.alert('登录已过期，请重新登录')
      }
    }
    // 其他错误提示
    const detail = error.response?.data?.detail
    const msg = Array.isArray(detail)
      ? detail.map((e) => e?.msg || JSON.stringify(e)).join('；')
      : detail || '请求失败，请稍后重试'
    if (typeof window !== 'undefined') {
      window.alert(msg)
    }
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

export default request
