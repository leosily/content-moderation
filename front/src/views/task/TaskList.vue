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
      <div class="filters">
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option value="待审核">待审核</option>
          <option value="审核中">审核中</option>
          <option value="已完成">已完成</option>
          <option value="审核失败">审核失败</option>
          <option value="已撤销">已撤销</option>
        </select>
        <input v-model.trim="keywordFilter" placeholder="按任务标题搜索" />
        <input v-model="startTimeFilter" type="datetime-local" />
        <input v-model="endTimeFilter" type="datetime-local" />
        <button class="ghost-btn" @click="applyFilters">筛选</button>
        <button class="ghost-btn" @click="resetFilters">重置</button>
      </div>

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
            <button
              v-if="canCancel(t)"
              class="danger-btn"
              :disabled="cancellingTaskId === getTaskId(t)"
              @click="handleCancelTask(t)"
            >
              {{ cancellingTaskId === getTaskId(t) ? '撤销中...' : '撤销任务' }}
            </button>
            <button
              v-if="canDelete(t)"
              class="danger-btn"
              :disabled="deletingTaskId === getTaskId(t)"
              @click="handleDeleteTask(t)"
            >
              {{ deletingTaskId === getTaskId(t) ? '删除中...' : '删除任务' }}
            </button>
          </div>
        </div>
      </div>

      <div class="pager">
        <span class="muted">共 {{ total }} 条</span>
        <button class="ghost-btn" :disabled="page <= 1" @click="changePage(-1)">上一页</button>
        <span class="muted">第 {{ page }} / {{ totalPages }} 页</span>
        <button class="ghost-btn" :disabled="page >= totalPages" @click="changePage(1)">下一页</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cancelTask, deleteTask, getTaskList } from '../../api/user'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const tasks = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const statusFilter = ref('')
const keywordFilter = ref('')
const startTimeFilter = ref('')
const endTimeFilter = ref('')
const cancellingTaskId = ref(null)
const deletingTaskId = ref(null)

const totalPages = computed(() => {
  return Math.max(1, Math.ceil((total.value || 0) / pageSize.value))
})

function normalizeTasks(res) {
  // 兼容不同后端返回字段
  return (
    res?.items ||
    res?.data?.items ||
    res?.tasks ||
    res?.data?.tasks ||
    res?.data ||
    res ||
    []
  )
}

async function fetchTasks() {
  loading.value = true
  try {
    const skip = (page.value - 1) * pageSize.value
    const res = await getTaskList({
      skip,
      limit: pageSize.value,
      status: statusFilter.value || undefined,
      keyword: keywordFilter.value || undefined,
      start_time: startTimeFilter.value ? new Date(startTimeFilter.value).toISOString() : undefined,
      end_time: endTimeFilter.value ? new Date(endTimeFilter.value).toISOString() : undefined
    })
    tasks.value = normalizeTasks(res)
    total.value = Number(res?.total ?? res?.data?.total ?? tasks.value.length ?? 0)
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  fetchTasks()
}

function resetFilters() {
  statusFilter.value = ''
  keywordFilter.value = ''
  startTimeFilter.value = ''
  endTimeFilter.value = ''
  page.value = 1
  fetchTasks()
}

function changePage(delta) {
  const nextPage = page.value + delta
  if (nextPage < 1 || nextPage > totalPages.value) return
  page.value = nextPage
  fetchTasks()
}

function goAuditResult(task) {
  const taskId = getTaskId(task)
  if (!taskId) return
  router.push(`/audit/result/${taskId}`)
}

function getTaskId(task) {
  return task?.id || task?.task_id || task?.taskId
}

function canCancel(task) {
  const status = String(task?.status || task?.state || '')
  return status.includes('待审核') || status.includes('审核中')
}

function canDelete(task) {
  const status = String(task?.status || task?.state || '')
  return !status.includes('审核中')
}

async function handleCancelTask(task) {
  const taskId = getTaskId(task)
  if (!taskId) return

  if (typeof window !== 'undefined' && !window.confirm(`确定撤销任务 #${taskId} 吗？`)) {
    return
  }

  cancellingTaskId.value = taskId
  try {
    await cancelTask(taskId)
    await fetchTasks()
  } finally {
    cancellingTaskId.value = null
  }
}

async function handleDeleteTask(task) {
  const taskId = getTaskId(task)
  if (!taskId) return

  if (typeof window !== 'undefined' && !window.confirm(`确定删除任务 #${taskId} 吗？删除后不可恢复。`)) {
    return
  }

  deletingTaskId.value = taskId
  try {
    await deleteTask(taskId)
    await fetchTasks()
  } finally {
    deletingTaskId.value = null
  }
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
  if (s.includes('撤销')) return 'cancelled'
  return 'pending'
}

onMounted(() => {
  if (route.query?.status) {
    statusFilter.value = String(route.query.status)
  }
  if (route.query?.keyword) {
    keywordFilter.value = String(route.query.keyword)
  }
  fetchTasks()
})
</script>

<style scoped>
.list-wrap {
  width: min(1400px, calc(100% - clamp(24px, 6vw, 96px)));
  margin: 0 auto;
  padding: clamp(20px, 3vw, 36px) 0 clamp(28px, 4vw, 52px);
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
  font-size: clamp(26px, 2.4vw, 36px);
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
  flex-wrap: wrap;
}

.table-card {
  margin-top: 14px;
  border: 1px solid #e8ecfa;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 20px rgba(45, 64, 110, 0.06);
  overflow-x: auto;
}

.filters {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-bottom: 1px solid #edf1fb;
  flex-wrap: wrap;
}

.filters input,
.filters select {
  padding: 8px 10px;
  border: 1px solid #d9e0f2;
  border-radius: 8px;
  font-size: 14px;
}

.table {
  width: 100%;
  min-width: 760px;
}

.row {
  display: grid;
  grid-template-columns: 130px 1.5fr 1fr 190px;
  padding: clamp(12px, 1.2vw, 16px);
  border-top: 1px solid #edf1fb;
  align-items: center;
  gap: 10px;
}

.head-row {
  background: #f8faff;
  font-weight: 600;
  border-top: none;
}

.state {
  padding: clamp(16px, 2vw, 22px);
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

.status-pill.cancelled {
  background: #fef3c7;
  color: #92400e;
}

.status-pill.pending {
  background: #f3f4f6;
  color: #4b5563;
}

.muted {
  color: #666;
  font-size: clamp(13px, 1vw, 15px);
  margin-top: 6px;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid #edf1fb;
}

button {
  border: none;
  border-radius: 10px;
  padding: clamp(9px, 1vw, 12px) clamp(12px, 1.2vw, 16px);
  font-size: clamp(13px, 1vw, 15px);
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
  margin-left: 8px;
  background: #fee2e2;
  color: #b91c1c;
}

.ghost-btn:hover {
  background: #e1e7ff;
}

.danger-btn:hover {
  background: #fecaca;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.24);
}

@media (max-width: 900px) {
  .list-wrap {
    width: calc(100% - 24px);
    padding-top: 16px;
  }

  .table {
    min-width: 640px;
  }
}
</style>

