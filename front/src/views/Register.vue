<template>
  <div class="auth-layout">
    <section class="auth-card">
      <p class="badge">AI 内容审核平台</p>
      <h1>创建账号</h1>
      <p class="sub">几秒钟完成注册，开启内容审核</p>
      <form class="auth-form" @submit.prevent="onRegister">
        <label>
          邮箱
          <input v-model="form.email" placeholder="name@example.com" />
        </label>
        <label>
          用户名
          <input v-model="form.username" placeholder="请输入用户名" />
        </label>
        <label>
          密码
          <input v-model="form.password" type="password" placeholder="请输入密码" />
        </label>
        <button class="primary-btn" type="submit">创建账号</button>
      </form>
    </section>
    <p class="auth-tip">
      已有账号？
      <a @click.prevent="router.push('/login')" href="#">去登录</a>
    </p>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { userRegister } from '../api/user'

const router = useRouter()

const form = reactive({
  email: '',
  username: '',
  password: ''
})

async function onRegister() {
  const res = await userRegister({
    email: form.email,
    username: form.username,
    password: form.password
  })

  // 如果后端直接返回 token，则立即保存；否则直接跳转登录页
  const token =
    res?.access_token || res?.token || res?.accessToken || res?.data?.access_token || ''
  const userId = res?.user_id || res?.userId || res?.data?.user_id || ''
  const userInfo = res?.user || res?.userInfo || res?.data?.user || res?.data?.userInfo || null

  if (token) {
    localStorage.setItem('access_token', token)
    if (userId) localStorage.setItem('user_id', userId)
  }

  // 无论是否拿到 token，都跳转到登录页
  router.push('/login')
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
  width: min(580px, 100%);
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

