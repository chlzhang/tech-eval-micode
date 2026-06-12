# 前后端架构设计方案

## 技术选型

| 层级 | 技术方案 | 说明 |
|------|----------|------|
| **前端** | React 18 + TypeScript + Vite | 现代化构建，组件化开发 |
| **UI框架** | Ant Design 5 | 企业级UI组件库 |
| **后端** | Python FastAPI | 高性能异步框架 |
| **数据库** | SQLite | 轻量级，无需额外安装 |
| **存储** | 本地文件系统 | 简单可靠 |
| **认证** | JWT Token | 简单易维护 |
| **部署** | Docker + Nginx | 标准化部署 |

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx (反向代理)                          │
│                    https://eval.your-domain.com                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Compose                             │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │   Frontend (React)  │    │   Backend (FastAPI) │            │
│  │   Port: 3000        │───▶│   Port: 8000        │            │
│  │   - Ant Design      │    │   - API Routes      │            │
│  │   - 状态管理         │    │   - JWT Auth        │            │
│  │   - 文件上传         │    │   - 任务队列        │            │
│  └─────────────────────┘    └──────────┬──────────┘            │
│                                        │                        │
│                                        ▼                        │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │   SQLite Database   │    │   File Storage      │            │
│  │   - 用户表          │    │   - 上传文件        │            │
│  │   - 任务表          │    │   - 生成报告        │            │
│  │   - 报告表          │    │   - 临时文件        │            │
│  └─────────────────────┘    └─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 目录结构设计

```
tech-eval-platform/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── components/          # 通用组件
│   │   │   ├── Layout/          # 布局组件
│   │   │   ├── FileUpload/      # 文件上传
│   │   │   └── ReportViewer/    # 报告查看器
│   │   ├── pages/               # 页面
│   │   │   ├── Login/           # 登录页
│   │   │   ├── Dashboard/       # 仪表盘
│   │   │   ├── TaskCreate/      # 创建任务
│   │   │   ├── TaskList/        # 任务列表
│   │   │   └── ReportView/      # 报告查看
│   │   ├── services/            # API服务
│   │   ├── store/               # 状态管理
│   │   └── utils/               # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # 后端项目
│   ├── app/
│   │   ├── api/                 # API路由
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── tasks.py         # 任务接口
│   │   │   └── reports.py       # 报告接口
│   │   ├── core/                # 核心模块
│   │   │   ├── config.py        # 配置
│   │   │   ├── security.py      # 安全
│   │   │   └── database.py      # 数据库
│   │   ├── models/              # 数据模型
│   │   │   ├── user.py          # 用户模型
│   │   │   ├── task.py          # 任务模型
│   │   │   └── report.py        # 报告模型
│   │   ├── services/            # 业务逻辑
│   │   │   ├── auth_service.py  # 认证服务
│   │   │   ├── task_service.py  # 任务服务
│   │   │   └── eval_service.py  # 评估服务（复用现有代码）
│   │   └── schemas/             # Pydantic模型
│   │       ├── auth.py
│   │       ├── task.py
│   │       └── report.py
│   ├── main.py                  # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml           # Docker编排
├── nginx.conf                   # Nginx配置
└── deploy.sh                    # 部署脚本
```

---

## 核心功能设计

### 1. 用户认证

```
POST /api/auth/login      # 用户登录，返回JWT Token
POST /api/auth/register   # 用户注册（管理员）
GET  /api/auth/me         # 获取当前用户信息
```

### 2. 任务管理

```
POST   /api/tasks              # 创建评估任务
GET    /api/tasks               # 获取任务列表
GET    /api/tasks/{id}          # 获取任务详情
DELETE /api/tasks/{id}          # 删除任务
POST   /api/tasks/{id}/start    # 启动任务
POST   /api/tasks/{id}/cancel   # 取消任务
GET    /api/tasks/{id}/progress # 获取任务进度
```

### 3. 文件管理

```
POST   /api/files/upload        # 上传文件
GET    /api/files/{id}          # 下载文件
DELETE /api/files/{id}          # 删除文件
```

### 4. 报告管理

```
GET    /api/reports              # 获取报告列表
GET    /api/reports/{id}         # 获取报告详情
GET    /api/reports/{id}/html    # 获取HTML报告
GET    /api/reports/{id}/docx    # 下载Word报告
GET    /api/reports/{id}/data    # 获取图表数据
DELETE /api/reports/{id}         # 删除报告
```

---

## 数据库设计

### 用户表 (users)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    display_name VARCHAR(100),
    department VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',  -- admin, user
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### 任务表 (tasks)

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    version VARCHAR(20) DEFAULT 'compact', -- compact, full
    progress FLOAT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 文件表 (files)

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id),
    filename VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 报告表 (reports)

```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id),
    title VARCHAR(200),
    tech_topic VARCHAR(100),
    version VARCHAR(20),
    html_path VARCHAR(500),
    docx_path VARCHAR(500),
    data_path VARCHAR(500),
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 前端页面设计

### 1. 登录页

```
┌─────────────────────────────────────────┐
│                                         │
│           技术交流评估报告生成器          │
│                                         │
│         ┌─────────────────┐             │
│         │    用户名        │             │
│         └─────────────────┘             │
│         ┌─────────────────┐             │
│         │    密码          │             │
│         └─────────────────┘             │
│                                         │
│         [    登  录    ]                │
│                                         │
└─────────────────────────────────────────┘
```

### 2. 仪表盘

```
┌─────────────────────────────────────────────────────────────┐
│  Logo    技术交流评估报告生成器           用户名 | 退出     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                   │
│  │ 总任务 │  │ 进行中 │  │ 已完成 │  │ 失败  │                │
│  │  12   │  │   2   │  │   9   │  │   1   │                │
│  └──────┘  └──────┘  └──────┘  └──────┘                   │
│                                                             │
│  最近任务                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 任务名称          │ 状态    │ 进度  │ 创建时间       │   │
│  ├───────────────────┼─────────┼───────┼───────────────│   │
│  │ 餐厨饲料化评估    │ 已完成  │ 100%  │ 2024-12-15    │   │
│  │ 热解技术评估      │ 进行中  │  65%  │ 2024-12-16    │   │
│  └───────────────────┴─────────┴───────┴───────────────┘   │
│                                                             │
│  [新建评估任务]                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. 创建任务页

```
┌─────────────────────────────────────────────────────────────┐
│                    新建评估任务                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  任务名称：[________________________________]                │
│                                                             │
│  报告版本：○ 精简版（4章）  ○ 完整版（8章）                   │
│                                                             │
│  会议转写文本：┌─────────────────────────┐                  │
│               │                         │                  │
│               │  拖拽文件到此处或点击上传  │                  │
│               │                         │                  │
│               └─────────────────────────┘                  │
│               支持 .md .pdf .docx 格式                      │
│                                                             │
│  对方技术文档：┌─────────────────────────┐                  │
│               │  拖拽文件到此处或点击上传  │                  │
│               └─────────────────────────┘                  │
│               （可选）                                      │
│                                                             │
│  基准参考文档：┌─────────────────────────┐                  │
│               │  拖拽文件到此处或点击上传  │                  │
│               └─────────────────────────┘                  │
│               （可选）                                      │
│                                                             │
│                    [创建并开始评估]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. 报告查看页

```
┌─────────────────────────────────────────────────────────────┐
│  餐厨剩余物饲料化技术评估报告          [下载Word] [下载PDF]  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │ 执行摘要 │ 交流背景 │ 技术主张 │ 基准对照 │ 初步结论 │   │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │            报告内容（HTML渲染）                       │   │
│  │                                                     │   │
│  │    - 图表交互                                       │   │
│  │    - 折叠展开                                       │   │
│  │    - 锚点导航                                       │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  质量评分：85分 (B级)                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ 事实与判断分离    ✓ 数值准确性                     │   │
│  │ ⚠ 冲突检测          ✓ 来源标注                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 部署方案

### Docker Compose 配置

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - DATABASE_URL=sqlite:///./data/eval.db
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000}
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

### Nginx 配置

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    server {
        listen 80;
        server_name eval.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name eval.your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # 前端
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # 后端API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            client_max_body_size 50M;
        }

        # 静态文件
        location /uploads/ {
            alias /var/www/uploads/;
        }
    }
}
```

---

## 实施计划

| 阶段 | 任务 | 工时 | 产出 |
|------|------|------|------|
| **第一阶段** | 后端API开发 | 3天 | FastAPI接口 |
| **第二阶段** | 前端页面开发 | 4天 | React应用 |
| **第三阶段** | 联调测试 | 2天 | 功能完整 |
| **第四阶段** | 部署上线 | 1天 | 可访问 |
| **总计** | | **10天** | |

---

## 成本估算

| 项目 | 费用 | 说明 |
|------|------|------|
| 云服务器 | 100-300元/月 | 2核4G足够 |
| 域名 | 50-100元/年 | 可选 |
| SSL证书 | 免费 | Let's Encrypt |
| **总计** | **约200元/月** | |

---

## 优势与风险

### 优势
- ✅ 复用现有后端核心代码（90%可复用）
- ✅ 技术栈成熟，学习成本低
- ✅ 部署简单，维护成本低
- ✅ 可逐步迭代，先上线核心功能

### 风险与应对
- ⚠️ 并发性能有限 → 任务队列异步处理
- ⚠️ 数据安全性 → HTTPS + JWT + 权限控制
- ⚠️ 文件存储空间 → 定期清理过期文件

---

是否同意此方案？如需调整任何部分请告诉我。
