<template>
  <div class="result-wrap">
    <header class="head">
      <div>
        <p class="badge">审核中心</p>
        <h1>审核结果</h1>
      </div>
      <div class="actions">
        <button class="ghost-btn" @click="router.push('/task/list')">返回任务列表</button>
      </div>
    </header>

    <div class="meta-card">
      <span>任务ID</span>
      <strong>#{{ taskId }}</strong>
    </div>

    <section v-if="loading" class="state">加载中...</section>

    <section v-else class="list">
      <div v-if="results.length === 0" class="state">暂无审核结果</div>

      <div v-else class="result-list">
        <div v-for="(r, idx) in results" :key="r.id || r.result_id || idx" class="item">
          <div class="item-head">
            <span class="pill" :class="statusClass(r.status)">{{ r.status || '-' }}</span>
            <span class="id">结果 #{{ r.id || idx + 1 }}</span>
          </div>

          <div class="item-row">
            <div class="label">违规类型</div>
            <div class="value">{{ r.violate_type || '-' }}</div>
          </div>
          <div class="item-row">
            <div class="label">审核内容</div>
            <div class="value pre">{{ r.content || '-' }}</div>
          </div>
          <div class="item-row">
            <div class="label">违规详情</div>
            <div class="value pre">{{ r.violate_detail || '-' }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAuditResults } from '../../api/user'

const router = useRouter()

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  }
})

const loading = ref(false)
const results = ref([])

const taskId = computed(() => props.taskId)

function normalizeResults(res) {
  return (
    res?.results ||
    res?.data?.results ||
    res?.items ||
    res?.data?.items ||
    res?.data ||
    res ||
    []
  )
}

async function fetchResults() {
  loading.value = true
  try {
    const res = await getAuditResults(taskId.value)
    results.value = normalizeResults(res)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchResults()
})

function statusClass(status) {
  const s = String(status || '')
  if (s.includes('通过')) return 'ok'
  if (s.includes('违规')) return 'violate'
  return 'pending'
}
</script>

<style scoped>
.result-wrap {
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

.meta-card {
  margin-top: 14px;
  display: inline-flex;
  gap: 10px;
  align-items: center;
  background: #eef2ff;
  color: #3730a3;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
}

.state {
  padding: 18px;
  color: #6b7280;
}

.list {
  margin-top: 12px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.item {
  border: 1px solid #e8ecfa;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 20px rgba(45, 64, 110, 0.06);
  padding: 14px;
}

.item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.pill {
  display: inline-flex;
  align-items: center;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
}

.pill.ok {
  background: #dcfce7;
  color: #166534;
}

.pill.violate {
  background: #fee2e2;
  color: #b91c1c;
}

.pill.pending {
  background: #e5e7eb;
  color: #4b5563;
}

.id {
  color: #6b7280;
  font-size: 12px;
}

.item-row {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 10px;
  margin-top: 8px;
}
.item-row:first-child {
  margin-top: 0;
}
.label {
  color: #888;
  font-size: 13px;
}
.value {
  font-size: 14px;
}
.pre {
  white-space: pre-wrap;
}

button {
  border: none;
  border-radius: 10px;
  padding: 9px 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ghost-btn {
  background: #eef2ff;
  color: #374151;
}

.ghost-btn:hover {
  background: #e1e7ff;
}

@media (max-width: 720px) {
  .item-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>

