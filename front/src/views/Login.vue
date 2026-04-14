<template>
  <div class="auth-layout">
    <section class="auth-card">
      <p class="badge">AI 内容审核平台</p>
      <h1>欢迎登录</h1>
      <p class="sub">使用账号快速进入任务中心</p>
      <form class="auth-form" @submit.prevent="onLogin">
        <label>
          邮箱
          <input v-model="form.email" placeholder="name@example.com" />
        </label>
        <label>
          密码
          <input v-model="form.password" type="password" placeholder="请输入密码" />
        </label>
        <button class="primary-btn" type="submit">登录</button>
      </form>
    </section>
    <p class="auth-tip">
      还没有账号？
      <a @click.prevent="router.push('/register')" href="#">立即注册</a>
    </p>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { userLogin } from '../api/user'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  email: '',
  password: ''
})

async function onLogin() {
  if (!form.email?.trim() || !form.password) {
    window.alert('请先输入邮箱和密码')
    return
  }
  const res = await userLogin({
    email: form.email,
    password: form.password
  })

  const token =
    res?.access_token || res?.token || res?.accessToken || res?.data?.access_token || ''
  const userId = res?.user_id || res?.userId || res?.data?.user_id || ''
  const userInfo = res?.user || res?.userInfo || res?.data?.user || res?.data?.userInfo || null

  userStore.saveUserInfo(userInfo, token, userId)

  // 如果接口没有直接返回 user 信息，兜底拉取一次
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (e) {
      // fetchUserInfo 失败时由 request 拦截器/alert 提示；这里不再额外处理
      console.error(e)
    }
  }

  router.push('/home')
}
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: clamp(18px, 3vw, 40px);
}

.auth-card {
  width: min(560px, 100%);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid #e8ecfa;
  box-shadow: 0 10px 30px rgba(26, 42, 82, 0.08);
  border-radius: 18px;
  padding: clamp(22px, 3vw, 34px);
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 999px;
  font-size: 12px;
  margin: 0 0 10px;
}

h1 {
  margin: 0;
  font-size: clamp(28px, 2.8vw, 40px);
}

.sub {
  margin: 8px 0 18px;
  color: #6b7280;
  font-size: clamp(14px, 1.2vw, 17px);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: clamp(13px, 1vw, 15px);
  color: #4b5563;
}

.auth-form input {
  border: 1px solid #d9e0f2;
  border-radius: 10px;
  padding: clamp(10px, 1.1vw, 13px) clamp(12px, 1.2vw, 15px);
  font-size: clamp(14px, 1vw, 16px);
  outline: none;
}

.auth-form input:focus {
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.primary-btn {
  margin-top: 4px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  color: #fff;
  font-size: clamp(14px, 1.05vw, 16px);
  font-weight: 600;
  padding: clamp(11px, 1.2vw, 14px);
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.24);
}

.auth-tip {
  margin-top: 14px;
  font-size: clamp(13px, 1vw, 15px);
  color: #6b7280;
}

.auth-tip a {
  color: #4f46e5;
  text-decoration: none;
  cursor: pointer;
}

@media (max-width: 480px) {
  .auth-card {
    padding: 22px;
  }

  h1 {
    font-size: 24px;
  }
}
</style>

