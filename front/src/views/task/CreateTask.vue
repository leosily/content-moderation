<template>
  <div class="create-wrap">
    <header class="top">
      <div>
        <p class="badge">任务中心</p>
        <h1>创建审核任务</h1>
      </div>
      <div class="top-actions">
        <button class="ghost-btn" @click="router.push('/home')">返回首页</button>
        <button class="ghost-btn" @click="router.push('/task/list')">任务列表</button>
      </div>
    </header>

    <section class="card">
      <h2>单条任务</h2>
      <p>提交一条文本，立即进入审核流程。</p>
      <input v-model="single.title" placeholder="任务标题" />
      <textarea v-model="single.content" placeholder="输入需要审核的内容" rows="6" />
      <button class="primary-btn" :disabled="loading" @click="createSingle">提交单条任务</button>
    </section>

    <section class="card">
      <h2>批量任务（CSV 上传）</h2>
      <p>支持上传 CSV 文件，按行批量审核。</p>
      <input v-model="batchTitle" placeholder="批量任务标题" />
      <input class="file-input" type="file" accept=".csv" @change="onFileChange" />
      <button class="primary-btn" :disabled="loading || !batchFile" @click="createBatch">
        提交批量任务
      </button>
    </section>

    <div class="tip">提示：CSV 第一列会作为审核文本内容。</div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createBatchTask, createSingleTask } from '../../api/user'

const router = useRouter()

const loading = ref(false)
const batchFile = ref(null)
const batchTitle = ref('')

const single = reactive({
  title: '',
  content: ''
})

function onFileChange(e) {
  const file = e.target.files?.[0]
  batchFile.value = file || null
}

async function createSingle() {
  loading.value = true
  try {
    await createSingleTask({
      title: single.title,
      content: single.content
    })
    router.push('/task/list')
  } finally {
    loading.value = false
  }
}

async function createBatch() {
  if (!batchFile.value) return
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('title', batchTitle.value)
    formData.append('file', batchFile.value)
    await createBatchTask(formData)
    router.push('/task/list')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 20px 40px;
}

.top {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
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

h1 {
  margin: 8px 0 0;
}

.top-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.card {
  margin: 16px 0;
  padding: 20px;
  border: 1px solid #e8ecfa;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 20px rgba(45, 64, 110, 0.06);
}

.card h2 {
  margin: 0;
}

.card p {
  margin: 6px 0 14px;
  color: #6b7280;
}

textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9e0f2;
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  min-height: 120px;
}

.card input {
  width: 100%;
  padding: 10px 12px;
  font-size: 14px;
  border: 1px solid #d9e0f2;
  border-radius: 10px;
  outline: none;
}

.card input:focus,
textarea:focus {
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.file-input {
  background: #fff;
}

button {
  margin-top: 12px;
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
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

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.24);
}

.ghost-btn:hover {
  background: #e1e7ff;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tip {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}

@media (min-width: 960px) {
  .create-wrap {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "top top"
      "single batch"
      "tip tip";
    gap: 16px;
  }

  .top {
    grid-area: top;
    margin-bottom: 0;
  }

  .card:first-of-type {
    grid-area: single;
    margin: 0;
  }

  .card:last-of-type {
    grid-area: batch;
    margin: 0;
  }

  .tip {
    grid-area: tip;
  }
}
</style>
