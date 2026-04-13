<template>
  <div class="home-wrap">
    <header class="hero">
      <div>
        <p class="badge">控制台</p>
        <h1>AI 内容审核工作台</h1>
        <p class="sub">统一创建任务、跟踪进度并查看审核结果</p>
      </div>
      <div class="hero-actions">
        <button class="primary-btn" @click="goCreateTask">创建审核任务</button>
        <button class="ghost-btn" @click="goTaskList">查看任务列表</button>
        <button class="danger-btn" @click="logout">退出登录</button>
      </div>
    </header>

    <section class="grid">
      <article class="panel">
        <h2>快捷入口</h2>
        <p>快速进入常用模块，提高审核效率。</p>
        <div class="panel-actions">
          <button class="primary-btn" @click="goCreateTask">新建任务</button>
          <button class="ghost-btn" @click="goTaskList">任务总览</button>
        </div>
      </article>
      <article class="panel">
        <h2>当前用户信息</h2>
        <div class="user-meta">
          <div><span>用户名</span><strong>{{ safeUserValue('username') }}</strong></div>
          <div><span>邮箱</span><strong>{{ safeUserValue('email') }}</strong></div>
          <div><span>手机号</span><strong>{{ safeUserValue('phone') }}</strong></div>
        </div>
        <pre>{{ userStore.userInfo }}</pre>
      </article>
    </section>    
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (e) {
      console.error(e)
    }
  }
})

function goCreateTask() {
  router.push('/task/create')
}

function goTaskList() {
  router.push('/task/list')
}

function logout() {
  userStore.clearUserInfo()
  router.push('/login')
}

function safeUserValue(key, fallback = '-') {
  return userStore.userInfo?.[key] ?? fallback
}
</script>

<style scoped>
.home-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 20px 40px;
}

.hero {
  background: linear-gradient(135deg, #1e293b, #1d4ed8);
  color: #fff;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 20px;
}

h1 {
  margin: 8px 0 6px;
  font-size: 30px;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.2);
  margin: 0;
}

.sub {
  margin: 0;
  opacity: 0.88;
}

.hero-actions,
.panel-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 16px;
}

.panel {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #e8ecfa;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 8px 20px rgba(45, 64, 110, 0.06);
}

.panel h2 {
  margin: 0 0 8px;
}

.panel p {
  margin: 0 0 14px;
  color: #6b7280;
}

button {
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-btn {
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  color: #fff;
}

.ghost-btn {
  background: #eef2ff;
  color: #374151;
}

.danger-btn {
  background: #fee2e2;
  color: #b91c1c;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.24);
}

.ghost-btn:hover {
  background: #e1e7ff;
}

.danger-btn:hover {
  background: #fecaca;
}

.user-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.user-meta div {
  background: #f8faff;
  border: 1px solid #e7ecfb;
  border-radius: 10px;
  padding: 10px;
}

.user-meta span {
  display: block;
  font-size: 12px;
  color: #6b7280;
}

.user-meta strong {
  font-size: 14px;
  color: #1f2937;
}

pre {
  margin: 0;
  background: #f8faff;
  border: 1px solid #e7ecfb;
  border-radius: 10px;
  padding: 12px;
  overflow: auto;
  min-height: 90px;
}

@media (max-width: 640px) {
  h1 {
    font-size: 24px;
  }
}
</style>

