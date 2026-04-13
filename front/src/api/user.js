// src/api/user.js（用户相关接口）
import request from './request'

export const userRegister = (data) => {
  return request({
    url: '/user/register',
    method: 'post',
    data
  })
}

export const userLogin = (data) => {
  // 后端使用 OAuth2PasswordRequestForm，要求 x-www-form-urlencoded
  const form = new URLSearchParams({
    username: data?.email || '',
    password: data?.password || ''
  })
  return request({
    url: '/user/login',
    method: 'post',
    data: form,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}

export const getUserInfo = () => {
  return request({
    url: '/user/me',
    method: 'get'
  })
}

export const updateUserInfo = (data) => {
  return request({
    url: '/user/me',
    method: 'put',
    data
  })
}

// src/api/task.js（任务相关接口）

// 创建单条任务
export const createSingleTask = (data) => {
  return request({
    url: '/task/single',
    method: 'post',
    data
  })
}

// 创建批量任务（CSV上传）
export const createBatchTask = (formData) => {
  return request({
    url: '/task/batch',
    method: 'post',
    data: formData
  })
}

// 获取任务详情
export const getTaskDetail = (taskId) => {
  return request({
    url: `/task/${taskId}`,
    method: 'get'
  })
}

// 获取任务列表
export const getTaskList = (skip = 0, limit = 10) => {
  return request({
    // 后端任务列表是 GET "/"，加斜杠避免 FastAPI 重定向
    url: '/task/',
    method: 'get',
    params: { skip, limit }
  })
}

// 获取任务进度
export const getTaskProgress = (taskId) => {
  return request({
    url: `/task/${taskId}/progress`,
    method: 'get'
  })
}

// src/api/audit.js（审核结果相关接口）

// 获取任务的所有审核结果
export const getAuditResults = (taskId) => {
  return request({
    url: `/audit/task/${taskId}`,
    method: 'get'
  })
}
