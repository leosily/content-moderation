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
          <!--div><span>手机号</span><strong>{{ safeUserValue('phone') }}</strong></div-->
        </div>
        <div class="user-note">
          <p>当前账号已登录，可直接创建审核任务并查看任务进度。</p>
          <ul>
            <li>建议先创建单条任务验证审核流程。</li>
            <li>批量审核请使用 CSV 上传，适合大规模内容处理。</li>
            <li>审核完成后可在任务列表查看详细结果。</li>
          </ul>
        </div>
      </article>
    </section>

    <section class="overview">
      <article class="overview-card">
        <h3>标准审核流程</h3>
        <ol>
          <li>创建任务并填写待审核文本或上传 CSV。</li>
          <li>在任务列表中跟踪运行状态和处理进度。</li>
          <li>进入结果页查看命中标签与风险等级。</li>
          <li>根据结果进行人工复核与策略调整。</li>
        </ol>
      </article>
      <article class="overview-card">
        <h3>平台能力说明</h3>
        <div class="feature-list">
          <div>
            <span>内容类型</span>
            <strong>文本审核</strong>
          </div>
          <div>
            <span>处理方式</span>
            <strong>单条 + 批量</strong>
          </div>
          <div>
            <span>结果追踪</span>
            <strong>任务列表可回溯</strong>
          </div>
          <div>
            <span>协作方式</span>
            <strong>机审 + 人工复核</strong>
          </div>
        </div>
      </article>
    </section>

    <section class="dashboard">
      <div class="dashboard-head">
        <div>
          <p class="dashboard-badge">可视化中心</p>
          <h3>智能审核看板</h3>
        </div>
        <div class="dashboard-tools">
          <div class="range-switch">
            <button
              v-for="day in [7, 30]"
              :key="day"
              class="range-btn"
              :class="{ active: trendDays === day }"
              @click="changeTrendDays(day)"
            >
              近{{ day }}天
            </button>
          </div>
          <p class="dashboard-tip">支持鼠标拖拽缩放、图例筛选和结果导出</p>
        </div>
      </div>

      <div class="service-health" :class="healthClass">
        <span class="health-label">服务状态</span>
        <strong>{{ healthText }}</strong>
      </div>

      <div class="metrics-grid">
        <article v-for="metric in dashboardMetrics" :key="metric.label" class="metric-card">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <em>{{ metric.trend }}</em>
        </article>
      </div>

      <div class="chart-panel">
        <div class="chart-tabs">
          <button
            v-for="tab in chartTabs"
            :key="tab.key"
            class="tab-btn"
            :class="{ active: activeChart === tab.key }"
            @click="switchChart(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>
        <p class="chart-title">
          {{ currentChartTitle }}
          <span v-if="dashboardLoading" class="loading-flag">（同步中...）</span>
        </p>
        <div ref="chartRef" class="chart-canvas"></div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { useUserStore } from '../store/user'
import { getDashboardStats, getTaskHealth } from '../api/user'

const router = useRouter()
const userStore = useUserStore()
const chartRef = ref(null)
const activeChart = ref('taskTrend')
const dashboardLoading = ref(false)
const trendDays = ref(7)
const healthStatus = ref('checking')
let chartInstance = null

const dashboardMetrics = ref([
  { label: '任务总数', value: 1268, trend: '+12.4%' },
  { label: '审批通过数', value: 987, trend: '+8.7%' },
  { label: '待处理任务', value: 164, trend: '-3.2%' },
  { label: '驳回任务', value: 117, trend: '+1.9%' }
])

const dashboardChartData = ref({
  taskTrendLabels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  taskTrendTasks: [138, 152, 168, 194, 176, 162, 171],
  taskTrendApproved: [102, 118, 132, 151, 143, 129, 136],
  approvalRateLabels: ['内容安全', '涉政风险', '违规营销', '色情低俗', '辱骂攻击'],
  approvalRateValues: [95, 89, 84, 78, 73],
  riskDistribution: [
    { value: 502, name: '低风险' },
    { value: 318, name: '中风险' },
    { value: 149, name: '高风险' },
    { value: 87, name: '待复核' }
  ]
})

const chartTabs = [
  { key: 'taskTrend', label: '任务趋势' },
  { key: 'approvalRate', label: '违规类型占比' },
  { key: 'riskDistribution', label: '风险分布' }
]

const currentChartTitle = computed(() => {
  return chartTabs.find((item) => item.key === activeChart.value)?.label ?? ''
})
const healthText = computed(() => {
  if (healthStatus.value === 'ok') return '运行正常'
  if (healthStatus.value === 'error') return '异常'
  return '检测中'
})
const healthClass = computed(() => {
  return {
    ok: healthStatus.value === 'ok',
    error: healthStatus.value === 'error'
  }
})

onMounted(async () => {
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (e) {
      console.error(e)
    }
  }
  await fetchDashboardData()
  await fetchTaskHealth()
  await nextTick()
  initChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  if (chartInstance) {
    chartInstance.off('click', handleChartClick)
    chartInstance.dispose()
    chartInstance = null
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

async function fetchDashboardData() {
  dashboardLoading.value = true
  try {
    const res = await getDashboardStats(trendDays.value)
    const metrics = res?.metrics || {}
    const charts = res?.charts || {}
    const taskTrend = charts?.task_trend || {}
    const approvalRate = charts?.approval_rate || {}

    dashboardMetrics.value = [
      { label: '任务总数', value: metrics.total_tasks ?? 0, trend: '实时' },
      { label: '审批通过数', value: metrics.approved_count ?? 0, trend: '实时' },
      { label: '待处理任务', value: metrics.pending_tasks ?? 0, trend: '实时' },
      { label: '驳回任务', value: metrics.rejected_count ?? 0, trend: '实时' }
    ]

    dashboardChartData.value = {
      taskTrendLabels: taskTrend.labels || [],
      taskTrendTasks: taskTrend.tasks || [],
      taskTrendApproved: taskTrend.approved || [],
      approvalRateLabels: approvalRate.labels || [],
      approvalRateValues: approvalRate.values || [],
      riskDistribution: charts?.risk_distribution || []
    }
  } catch (error) {
    console.error('fetch dashboard stats failed:', error)
  } finally {
    dashboardLoading.value = false
  }
}

async function fetchTaskHealth() {
  healthStatus.value = 'checking'
  try {
    await getTaskHealth()
    healthStatus.value = 'ok'
  } catch (error) {
    console.error('fetch task health failed:', error)
    healthStatus.value = 'error'
  }
}

function changeTrendDays(days) {
  if (trendDays.value === days) return
  trendDays.value = days
  fetchDashboardData()
}

function switchChart(tab) {
  activeChart.value = tab
  renderChart()
}

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  chartInstance.off('click', handleChartClick)
  chartInstance.on('click', handleChartClick)
  renderChart()
}

function handleChartClick(params) {
  if (!params) return

  if (activeChart.value === 'approvalRate' && params.name && params.name !== '暂无数据') {
    router.push({
      path: '/task/list',
      query: { keyword: params.name }
    })
    return
  }

  if (activeChart.value === 'riskDistribution' && params.name === '待处理') {
    router.push({
      path: '/task/list',
      query: { status: '审核中' }
    })
  }
}

function resizeChart() {
  chartInstance?.resize()
}

function renderChart() {
  if (!chartInstance) return
  chartInstance.setOption(getChartOption(activeChart.value), true)
}

function getChartOption(tab) {
  const common = {
    tooltip: { trigger: 'axis' },
    legend: { top: 10, textStyle: { color: '#475569' } },
    toolbox: {
      right: 12,
      feature: {
        dataZoom: { yAxisIndex: 'none' },
        restore: {},
        saveAsImage: {}
      }
    },
    grid: { left: 44, right: 24, top: 64, bottom: 56 }
  }

  if (tab === 'taskTrend') {
    return {
      ...common,
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dashboardChartData.value.taskTrendLabels
      },
      yAxis: { type: 'value', axisLabel: { color: '#64748b' } },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { start: 0, end: 100, height: 20, bottom: 16 }
      ],
      series: [
        {
          name: '任务总数',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { width: 3, color: '#2563eb' },
          areaStyle: { color: 'rgba(37, 99, 235, 0.14)' },
          data: dashboardChartData.value.taskTrendTasks
        },
        {
          name: '审批通过数',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { width: 3, color: '#10b981' },
          areaStyle: { color: 'rgba(16, 185, 129, 0.12)' },
          data: dashboardChartData.value.taskTrendApproved
        }
      ]
    }
  }

  if (tab === 'approvalRate') {
    return {
      ...common,
      xAxis: {
        type: 'category',
        data: dashboardChartData.value.approvalRateLabels
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { formatter: '{value}%' }
      },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { start: 0, end: 100, height: 20, bottom: 16 }
      ],
      series: [
        {
          name: '占比',
          type: 'bar',
          barWidth: '38%',
          itemStyle: {
            borderRadius: [8, 8, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#38bdf8' },
              { offset: 1, color: '#2563eb' }
            ])
          },
          data: dashboardChartData.value.approvalRateValues
        }
      ]
    }
  }

  return {
    ...common,
    tooltip: { trigger: 'item' },
    legend: { top: 8, left: 'center' },
    series: [
      {
        name: '风险分布',
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['50%', '54%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{d}%' },
        data: dashboardChartData.value.riskDistribution
      }
    ]
  }
}
</script>

<style scoped>
.home-wrap {
  width: min(1400px, calc(100% - clamp(24px, 6vw, 96px)));
  margin: 0 auto;
  padding: clamp(20px, 3vw, 36px) 0 clamp(28px, 4vw, 52px);
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
  font-size: clamp(26px, 2.6vw, 38px);
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
  font-size: clamp(14px, 1.2vw, 17px);
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

.overview {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.overview-card {
  background: #fff;
  border: 1px solid #e8ecfa;
  border-radius: 16px;
  padding: clamp(16px, 2vw, 24px);
  box-shadow: 0 8px 20px rgba(45, 64, 110, 0.05);
}

.overview-card h3 {
  margin: 0 0 12px;
  font-size: clamp(18px, 1.4vw, 22px);
  color: #111827;
}

.overview-card ol {
  margin: 0;
  padding-left: 18px;
  color: #4b5563;
  font-size: clamp(13px, 1vw, 15px);
}

.overview-card li + li {
  margin-top: 8px;
}

.feature-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 10px;
}

.feature-list div {
  background: #f8faff;
  border: 1px solid #e7ecfb;
  border-radius: 10px;
  padding: 10px;
}

.feature-list span {
  display: block;
  font-size: clamp(12px, 0.9vw, 13px);
  color: #6b7280;
}

.feature-list strong {
  font-size: clamp(14px, 1.05vw, 16px);
  color: #1f2937;
}

.dashboard {
  margin-top: 16px;
  background: #fff;
  border: 1px solid #e8ecfa;
  border-radius: 16px;
  padding: clamp(16px, 2vw, 24px);
  box-shadow: 0 10px 26px rgba(45, 64, 110, 0.06);
}

.dashboard-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: end;
  gap: 12px;
  margin-bottom: 14px;
}

.dashboard-badge {
  margin: 0;
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: #1d4ed8;
  background: #dbeafe;
}

.dashboard-head h3 {
  margin: 8px 0 0;
  font-size: clamp(18px, 1.5vw, 24px);
  color: #0f172a;
}

.dashboard-tip {
  margin: 0;
  color: #64748b;
  font-size: clamp(12px, 0.95vw, 14px);
}

.service-health {
  margin-bottom: 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #f8fbff;
  color: #1e3a8a;
}

.service-health.ok {
  border-color: #bbf7d0;
  background: #f0fdf4;
  color: #166534;
}

.service-health.error {
  border-color: #fecaca;
  background: #fef2f2;
  color: #b91c1c;
}

.health-label {
  font-size: 12px;
  opacity: 0.85;
}

.dashboard-tools {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.range-switch {
  display: inline-flex;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  overflow: hidden;
  background: #f8fbff;
}

.range-btn {
  border: none;
  background: transparent;
  color: #475569;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.range-btn.active {
  background: #2563eb;
  color: #fff;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 10px;
}

.metric-card {
  background: linear-gradient(145deg, #f8faff, #f1f5ff);
  border: 1px solid #e6ebff;
  border-radius: 12px;
  padding: 12px;
}

.metric-card span {
  display: block;
  color: #64748b;
  font-size: clamp(12px, 0.9vw, 13px);
}

.metric-card strong {
  display: block;
  margin-top: 6px;
  color: #111827;
  font-size: clamp(22px, 2vw, 30px);
  line-height: 1;
}

.metric-card em {
  display: inline-block;
  margin-top: 8px;
  font-style: normal;
  color: #2563eb;
  font-size: clamp(12px, 0.9vw, 13px);
}

.chart-panel {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid #e8ecfa;
  border-radius: 14px;
  background: #fcfdff;
}

.chart-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tab-btn {
  padding: 8px 14px;
  border: 1px solid #dbe3fb;
  border-radius: 999px;
  background: #fff;
  color: #475569;
  font-size: 14px;
  font-weight: 600;
}

.tab-btn.active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.28);
}

.chart-title {
  margin: 12px 0 0;
  font-size: 14px;
  color: #64748b;
}

.loading-flag {
  color: #2563eb;
}

.chart-canvas {
  width: 100%;
  height: clamp(300px, 36vw, 420px);
}

.panel {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #e8ecfa;
  border-radius: 16px;
  padding: clamp(16px, 2vw, 24px);
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
  padding: clamp(10px, 1.1vw, 13px) clamp(14px, 1.4vw, 18px);
  font-size: clamp(14px, 1vw, 16px);
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
  font-size: clamp(12px, 0.9vw, 13px);
  color: #6b7280;
}

.user-meta strong {
  font-size: clamp(14px, 1.1vw, 16px);
  color: #1f2937;
}

.user-note {
  margin: 0;
  background: #f8faff;
  border: 1px solid #e7ecfb;
  border-radius: 10px;
  padding: 12px 14px;
}

.user-note p {
  margin: 0;
  color: #4b5563;
  font-size: clamp(13px, 1vw, 15px);
}

.user-note ul {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #4b5563;
  font-size: clamp(13px, 1vw, 15px);
}

.user-note li + li {
  margin-top: 6px;
}

@media (max-width: 640px) {
  .home-wrap {
    width: calc(100% - 24px);
    padding-top: 16px;
  }

  h1 {
    font-size: 24px;
  }

  .chart-panel {
    padding: 10px;
  }
}
</style>

