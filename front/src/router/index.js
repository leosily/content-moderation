import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Home from '../views/Home.vue'
import CreateTask from '../views/task/CreateTask.vue'
import TaskList from '../views/task/TaskList.vue'
import AuditResult from '../views/audit/AuditResult.vue'

// 路由守卫：未登录跳转至登录页
const requireAuth = (to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    next()
  } else {
    next('/login')
  }
}

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录 - AI内容审核系统' }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { title: '注册 - AI内容审核系统' }
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: { title: '首页 - AI内容审核系统' },
    beforeEnter: requireAuth
  },
  {
    path: '/task/create',
    name: 'CreateTask',
    component: CreateTask,
    meta: { title: '创建审核任务 - AI内容审核系统' },
    beforeEnter: requireAuth
  },
  {
    path: '/task/list',
    name: 'TaskList',
    component: TaskList,
    meta: { title: '任务列表 - AI内容审核系统' },
    beforeEnter: requireAuth
  },
  {
    path: '/audit/result/:taskId',
    name: 'AuditResult',
    component: AuditResult,
    meta: { title: '审核结果 - AI内容审核系统' },
    beforeEnter: requireAuth,
    props: true  // 接收taskId参数
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由跳转时修改页面标题
router.beforeEach((to) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
})

export default router
