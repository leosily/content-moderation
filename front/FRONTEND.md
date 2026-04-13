# 前端实现说明（Vue3 + Vite + Pinia + Vue Router + Axios）

本项目的前端位于 `front/`，采用 **Vue 3（Composition API）** + **Vite** 构建，状态管理使用 **Pinia**，路由使用 **Vue Router**，与后端交互使用 **Axios**（封装在 `src/api/request.js`）。

> 后端路由前缀：`/api`  
> 前端默认请求地址：`http://localhost:8000/api`（见 `src/api/request.js`）

---

## 目录结构与职责

```
front/
  index.html                 # Vite 入口 HTML
  vite.config.js             # Vite 配置
  package.json               # 前端依赖与脚本
  src/
    main.js                  # 应用入口：创建 app、挂载 pinia/router
    App.vue                  # 根组件：全局背景/基础样式 + 承载 router-view
    router/
      index.js               # 路由表 + 路由守卫（鉴权）
    store/
      user.js                # Pinia 用户状态：token、userInfo、userId
    api/
      request.js             # Axios 实例 + 请求/响应拦截器
      user.js                # 所有接口封装（user/task/audit）
    views/
      Login.vue              # 登录页
      Register.vue           # 注册页
      Home.vue               # 控制台首页
      task/
        CreateTask.vue       # 创建任务（单条/批量）
        TaskList.vue         # 任务列表
      audit/
        AuditResult.vue      # 审核结果页
```

---

## 启动与构建

在 Windows PowerShell 中：

```powershell
cd "E:\content moderation\front"
npm install
npm run dev
```

生产构建：

```powershell
npm run build
```

---

## 应用入口（`src/main.js`）

`src/main.js` 做了三件事：

1. `createApp(App)` 创建 Vue 应用
2. `.use(createPinia())` 注册 Pinia
3. `.use(router)` 注册路由
4. `.mount('#app')` 挂载到 `index.html` 的 `<div id="app"></div>`

入口文件保持极简，业务都放在 `views/` 与 `store/` 中。

---

## 根组件与全局样式（`src/App.vue`）

`App.vue` 的目标是：

- 提供全局背景（渐变/淡色）与基础样式（字体、box-sizing）
- 渲染 `<router-view />` 作为所有页面的容器

项目没有引入 UI 框架（Element Plus 等），页面样式通过各 `.vue` 的 scoped CSS 实现，并在 `App.vue` 放少量全局 CSS 让整体更统一。

---

## 路由系统与鉴权（`src/router/index.js`）

### 1）路由表

路由已定义：

- `/login` 登录
- `/register` 注册
- `/home` 首页（需要登录）
- `/task/create` 创建任务（需要登录）
- `/task/list` 任务列表（需要登录）
- `/audit/result/:taskId` 审核结果（需要登录）

### 2）路由守卫 requireAuth

核心逻辑：

- 读取 `localStorage.getItem('access_token')`
- 如果有 token：允许进入
- 如果没有：跳转到 `/login`

这保证了用户必须登录才能进入业务页。

### 3）页面标题

通过 `router.beforeEach` 读取 `to.meta.title` 并设置 `document.title`，实现路由级标题。

---

## 用户状态管理（`src/store/user.js`）

Pinia store 负责管理：

- `token`：JWT access token（来自 `localStorage`)
- `userId`：用户 id（来自 `localStorage`)
- `userInfo`：当前用户信息对象（来自 `/user/me`）

### 1）`saveUserInfo(userInfo, token, userId)`

- 写入 store state
- 将 `access_token` / `user_id` 持久化到 `localStorage`

### 2）`clearUserInfo()`

- 清空 store state
- 清除 `localStorage` 中的 token 与 user_id

### 3）`fetchUserInfo()`

- 若无 token：直接返回 `null`
- 调用 `getUserInfo()`（`GET /api/user/me`）
- 将返回的用户对象写入 `userInfo`，并尝试写入 `userId`
- 若请求失败（例如 401）：清空本地登录态并把错误抛出

这让页面只要在 `onMounted` 时调用一次 `fetchUserInfo()` 就能拿到用户信息。

---

## Axios 封装与错误处理（`src/api/request.js`）

### 1）axios 实例

```js
axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000
})
```

注意：这里**没有全局强制 `Content-Type: application/json`**，是为了兼容：

- JSON 请求（axios 会自动加 `application/json`）
- `x-www-form-urlencoded`（登录）
- `multipart/form-data`（CSV 上传 FormData）

### 2）请求拦截器：自动带 token

每次请求都会读取 `localStorage.getItem('access_token')`，并加到：

`Authorization: Bearer <token>`

这样后端 `get_current_user` 能从请求头拿到 JWT 并完成鉴权。

### 3）响应拦截器：统一处理异常

- 若状态码 `401`：
  - 清 token / user_id
  - 跳转 `/login`
  - `alert` 提示“登录已过期”
- 其他错误：
  - 尝试读取 `error.response.data.detail` 作为提示
  - `alert` 弹窗显示

> 这里采用浏览器原生 `alert`，避免引入 UI 框架依赖；你后续如果接入 Element Plus/Naive UI，可以把 `alert` 替换成更好的 toast/message 组件。

---

## API 模块（`src/api/user.js`）

为了减少文件数量，目前把三类接口放在同一个文件里导出：

- **用户**：`userRegister` / `userLogin` / `getUserInfo` / `updateUserInfo`
- **任务**：`createSingleTask` / `createBatchTask` / `getTaskDetail` / `getTaskList` / `getTaskProgress`
- **审核结果**：`getAuditResults`

### 1）注册：`POST /api/user/register`

请求体 JSON：

```json
{ "email": "...", "username": "...", "password": "..." }
```

后端返回 `UserResponse`（包含 `id/email/username/...`），前端注册成功后跳转登录页。

### 2）登录：`POST /api/user/login`

后端实现使用 `OAuth2PasswordRequestForm`，因此前端必须提交 `x-www-form-urlencoded`：

- 字段名固定为 `username` 与 `password`
- 其中 `username` 在你的后端被当作 email 使用

后端返回：

```json
{ "access_token": "...", "token_type": "bearer", "user_id": 1 }
```

前端会保存 token 并进入 `/home`。

### 3）任务列表：`GET /api/task/`

后端返回 `List[TaskResponse]`，因此前端 `TaskList.vue` 做了 normalize：

- 优先取 `res` 本身作为数组
- 兼容某些情况下的 `res.data/items` 等结构（可扩展）

### 4）批量任务：`POST /api/task/batch`

后端签名为：

`create_batch_task(title: str, file: UploadFile = File(...))`

因此前端 `FormData` 必须包含：

- `title`（字符串）
- `file`（CSV 文件）

---

## 页面实现与交互流程

### 1）登录页（`views/Login.vue`）

流程：

1. 用户输入 email + password
2. 调用 `userLogin({ email, password })`
3. 从返回值提取 `access_token/user_id`
4. 调 `userStore.saveUserInfo(...)`
5. 可选：若没有 userInfo，则调用 `userStore.fetchUserInfo()`
6. 跳转 `/home`

UI：采用居中卡片、主按钮、输入框 focus 高亮，并做了移动端适配与 hover 动效。

### 2）注册页（`views/Register.vue`）

流程：

1. 输入 email/username/password
2. `userRegister(...)`
3. 注册成功后跳转 `/login`

### 3）首页（`views/Home.vue`）

流程：

- `onMounted` 时若没有 `userInfo`，调用 `fetchUserInfo()`
- 提供三个动作：
  - 创建任务 -> `/task/create`
  - 查看任务 -> `/task/list`
  - 退出登录 -> 清理 store/localStorage -> `/login`

### 4）创建任务（`views/task/CreateTask.vue`）

单条任务：

- 输入 `title` + `content`
- 调用 `createSingleTask({ title, content })`
- 成功后进入任务列表

批量任务：

- 输入 `batchTitle` + 选择 CSV 文件
- 构造 `FormData(title, file)`
- 调用 `createBatchTask(formData)`
- 成功后进入任务列表

UI：桌面端双栏（单条/批量），小屏自动变单列。

### 5）任务列表（`views/task/TaskList.vue`）

- `onMounted` 调用 `getTaskList(skip=0, limit=10)`
- 展示：任务 id、状态、进度、创建时间
- 状态采用“胶囊”展示（根据中文状态文案映射颜色）
- 在窄屏下会隐藏创建时间列，提升可读性

### 6）审核结果（`views/audit/AuditResult.vue`）

- 从路由 `props` 获取 `taskId`
- 请求 `getAuditResults(taskId)`（后端返回 `BatchAuditResponse`）
- 展示每条审核结果的：
  - `status`（通过/违规）→ 状态胶囊
  - `violate_type`
  - `content`
  - `violate_detail`

---

## 你后续可以怎么扩展（建议）

- **把 API 拆分文件**：`api/user.js` / `api/task.js` / `api/audit.js`，更清晰
- **把通用 UI 抽组件**：按钮、卡片、状态胶囊、空状态、加载态
- **把 baseURL 做成环境变量**：
  - `.env.development`：`VITE_API_BASE=http://localhost:8000/api`
  - `request.js` 使用 `import.meta.env.VITE_API_BASE`
- **把 alert 替换成 toast**：接入 Element Plus / Naive UI / Arco 等

