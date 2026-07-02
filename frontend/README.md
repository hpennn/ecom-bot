# 电商客服机器人管理后台前端

基于 Vue 3 + Vite + Element Plus 构建的电商客服机器人管理后台前端项目。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 新一代前端构建工具
- **Vue Router** - Vue.js 官方路由管理器
- **Pinia** - Vue.js 的状态管理库
- **Element Plus** - 基于 Vue 3 的组件库
- **Axios** - HTTP 请求库

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口封装
│   │   ├── auth.js       # 认证相关接口
│   │   ├── stores.js     # 店铺管理接口
│   │   ├── knowledge.js  # 知识库接口
│   │   └── conversations.js  # 对话管理接口
│   ├── components/       # 公共组件
│   ├── layouts/         # 布局组件
│   │   └── MainLayout.vue  # 主布局（侧边栏 + 顶部导航）
│   ├── pages/           # 页面组件
│   │   ├── Login.vue     # 登录页
│   │   ├── Register.vue  # 注册页
│   │   ├── Dashboard.vue  # 仪表盘
│   │   ├── Stores.vue    # 店铺管理列表
│   │   ├── StoreCreate.vue  # 创建店铺
│   │   ├── StoreDetail.vue  # 店铺详情
│   │   ├── Knowledge.vue  # 知识库管理
│   │   ├── Conversations.vue  # 对话记录列表
│   │   ├── ConversationDetail.vue  # 对话详情
│   │   └── Settings.vue  # 系统设置
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── stores/           # Pinia 状态管理
│   │   ├── auth.js      # 认证状态
│   │   ├── store.js     # 店铺状态
│   │   └── knowledge.js  # 知识库状态
│   ├── styles/          # 全局样式
│   │   └── main.css
│   ├── utils/           # 工具函数
│   │   └── request.js   # Axios 实例封装
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── .env.example         # 环境变量示例
├── index.html
├── package.json
└── vite.config.js       # Vite 配置
```

## 功能特性

### 1. 用户认证
- 用户登录/注册
- Token 存储在 localStorage
- 路由守卫保护

### 2. 仪表盘
- 统计卡片（店铺数、对话数、消息数、AI回复率）
- 最近对话列表
- 知识库分类统计

### 3. 店铺管理
- 店铺列表（卡片视图）
- 创建/编辑/删除店铺
- 支持平台：拼多多、淘宝、京东

### 4. 知识库管理
- 知识条目列表
- 分类筛选（FAQ、商品信息、售后政策、物流信息、自定义）
- 添加/编辑/删除知识
- 批量导入（CSV/Excel）
- 测试回复功能

### 5. 对话记录
- 对话列表（支持状态筛选）
- 对话详情（消息气泡展示）
- 手动回复覆盖 AI 回复
- 关闭对话

### 6. 系统设置
- 自动回复开关
- AI 回复风格（专业/亲切/简洁）
- 回复前缀/后缀
- 拼多多 API 配置
- 敏感词过滤
- 消息通知设置

## 安装与运行

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 4. 构建生产版本

```bash
npm run build
```

### 5. 预览生产构建

```bash
npm run preview
```

## API 接口

项目开发时配置了代理，会将 `/api` 请求代理到 `http://localhost:8000`。

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户 |

### 店铺接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/stores | 获取店铺列表 |
| POST | /api/stores | 创建店铺 |
| PUT | /api/stores/:id | 更新店铺 |
| DELETE | /api/stores/:id | 删除店铺 |

### 知识库接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/stores/:id/knowledge | 获取知识列表 |
| POST | /api/stores/:id/knowledge | 添加知识 |
| PUT | /api/knowledge/:id | 更新知识 |
| DELETE | /api/knowledge/:id | 删除知识 |
| POST | /api/stores/:id/knowledge/batch | 批量导入 |

### 对话接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/stores/:id/conversations | 获取对话列表 |
| GET | /api/conversations/:id/messages | 获取消息记录 |
| POST | /api/conversations/:id/reply | 发送回复 |
| POST | /api/stores/:id/reply | 测试回复 |

### 统计接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/stores/:id/stats | 获取店铺统计 |

## UI 设计

- **主色调**：蓝色系 (#409EFF)
- **布局**：左侧菜单栏 + 顶部导航栏
- **组件库**：Element Plus
- **界面语言**：中文
- **响应式**：支持移动端到桌面端

## 开发说明

### 请求拦截器

- 自动在请求头添加 `Authorization: Bearer {token}`
- 统一错误处理
- Token 过期自动跳转登录页

### 状态管理

- `auth` store：用户认证状态
- `store` store：店铺列表和当前选中店铺
- `knowledge` store：知识库列表和筛选状态

### 路由守卫

- 未登录访问需认证页面会跳转到登录页
- 已登录访问登录/注册页会跳转到仪表盘
- 页面标题自动设置

## License

MIT
