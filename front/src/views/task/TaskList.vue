<template>
  <div class="list-wrap">
    <header class="head">
      <div>
        <p class="badge">任务中心</p>
        <h1>任务列表</h1>
      </div>
      <div class="actions">
        <button class="primary-btn" @click="router.push('/task/create')">创建任务</button>
        <button class="ghost-btn" @click="router.push('/home')">返回首页</button>
      </div>
    </header>

    <section v-if="loading" class="state">加载中...</section>

    <section v-else class="table-card">
      <div v-if="tasks.length === 0" class="state">暂无任务</div>

      <div v-else class="table">
        <div class="row head-row">
          <div>ID</div>
          <div>状态/进度</div>
          <div>创建时间</div>
          <div>操作</div>
        </div>
        <div v-for="t in tasks" :key="t.id || t.task_id || t.taskId" class="row">
          <div class="mono">#{{ t.id || t.task_id || t.taskId }}</div>
          <div>
            <div class="status">
              <span class="status-pill" :class="statusClass(t.status || t.state)">{{ t.status || t.state || '-' }}</span>
            </div>
            <div class="muted">{{ formatProgress(t) }}</div>
          </div>
          <div class="muted">{{ t.created_at || '-' }}</div>
          <div>
            <button class="ghost-btn" @click="goAuditResult(t)">查看审核结果</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getTaskList } from '../../api/user'

const router = useRouter()

const loading = ref(false)
const tasks = ref([])

function normalizeTasks(res) {
  // 兼容不同后端返回字段
  return (
    res?.tasks ||
    res?.data?.tasks ||
    res?.items ||
    res?.data?.items ||
    res?.data ||
    res ||
    []
  )
}

async function fetchTasks() {
  loading.value = true
  try {
    const res = await getTaskList(0, 10)
    tasks.value = normalizeTasks(res)
  } finally {
    loading.value = false
  }
}

function goAuditResult(task) {
  const taskId = task?.id || task?.task_id || task?.taskId
  if (!taskId) return
  router.push(`/audit/result/${taskId}`)
}

function formatProgress(t) {
  const total = t.total_count ?? t.total ?? null
  const completed = t.completed_count ?? t.completed ?? null

  if (total === null || completed === null) return '—'
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0
  return `完成：${completed}/${total}（${percent}%）`
}

function statusClass(status) {
  const s = String(status || '')
  if (s.includes('完成')) return 'ok'
  if (s.includes('审核中')) return 'processing'
  if (s.includes('失败')) return 'error'
  return 'pending'
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.list-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 20px 40px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

h1 {
  margin: 8px 0 0;
}

.badge {
  display: inline-block;
  margin: 0;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4f46e5;
}

.actions {
  display: flex;
  gap: 10px;
}

.table-card {
  margin-top: 14px;
  border: 1px solid #e8ecfa;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 20px rgba(45, 64, 110, 0.06);
  overflow: hidden;
}

.table {
  width: 100%;
}

.row {
  display: grid;
  grid-template-columns: 120px 1.5fr 1fr 170px;
  padding: 12px;
  border-top: 1px solid #edf1fb;
  align-items: center;
  gap: 8px;
}

.head-row {
  background: #f8faff;
  font-weight: 600;
  border-top: none;
}

.state {
  padding: 18px;
  color: #6b7280;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: #4f46e5;
}

.status {
  font-weight: 600;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid transparent;
}

.status-pill.ok {
  background: #dcfce7;
  color: #166534;
}

.status-pill.processing {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-pill.error {
  background: #fee2e2;
  color: #b91c1c;
}

.status-pill.pending {
  background: #f3f4f6;
  color: #4b5563;
}

.muted {
  color: #666;
  font-size: 13px;
  margin-top: 6px;
}

button {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
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

.ghost-btn:hover {
  background: #e1e7ff;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.24);
}

@media (max-width: 900px) {
  .row {
    grid-template-columns: 100px 1fr;
  }

  .row > div:nth-child(3) {
    display: none;
  }
}
</style>

