import { defineStore } from 'pinia'
import { getUserInfo } from '../api/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null, // 用户信息
    token: localStorage.getItem('access_token') || '', // JWT令牌
    userId: localStorage.getItem('user_id') || '' // 用户ID
  }),
  actions: {
    // 保存用户信息和令牌
    saveUserInfo(userInfo, token, userId) {
      this.userInfo = userInfo || null
      this.token = token || ''
      this.userId = userId || ''

      if (this.token) localStorage.setItem('access_token', this.token)
      if (this.userId) localStorage.setItem('user_id', this.userId)
    },
    // 清除用户信息（退出登录）
    clearUserInfo() {
      this.userInfo = null
      this.token = ''
      this.userId = ''
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
    },
    // 获取当前用户信息
    async fetchUserInfo() {
      // token 有可能来自 localStorage；这里兜底读取一下
      if (!this.token) {
        const token = localStorage.getItem('access_token')
        if (token) this.token = token
      }

      // 未登录则不请求
      if (!this.token) return null

      try {
        const res = await getUserInfo()
        // 兼容不同后端返回结构
        const user = res?.user || res?.data || res || null
        const userId =
          user?.id ||
          user?.user_id ||
          localStorage.getItem('user_id') ||
          ''

        this.userInfo = user
        this.userId = userId

        const token = localStorage.getItem('access_token') || this.token
        if (token) this.token = token

        if (this.userId) localStorage.setItem('user_id', this.userId)
        return this.userInfo
      } catch (err) {
        // 登录过期/未授权等情况：清空本地状态由 request 拦截器兜底
        this.clearUserInfo()
        throw err
      }
    }
  }
})