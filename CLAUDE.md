# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

教培机构微信通知助手。教师在 Web 页面管理课程分组、学员、通知模板，通过 AppleScript (macOS) / pyautogui (Windows) 自动化操控微信，批量向家长发送个性化通知。AI（DeepSeek）根据概要实时扩展课程内容和学员表现评语。

## 架构

```
┌──────────────────────┐       HTTP/JSON        ┌──────────────────────┐
│  本地 Python 客户端    │ ◄──────────────────────► │  云端 Node.js 服务端   │
│  (Flask, 端口 5000)   │     JWT Bearer Token    │  (Express, 端口 5001) │
│  - Jinja2 页面渲染     │                         │  - REST API           │
│  - WeChat 自动化       │                         │  - JWT 认证            │
│  - 截图 / 拼长图       │                         │  - SQLite 数据库       │
│  - AI 生成（本地）      │                         │                       │
└──────────────────────┘                         └──────────────────────┘
```

```
server/                    # Node.js Express API (新增)
  package.json
  src/
    index.js               # 入口：Express + cors + 路由挂载
    config.js              # PORT, JWT_SECRET, DB_PATH
    db/
      connection.js        # better-sqlite3 单例 (WAL + FK)
      schema.js            # CREATE TABLE IF NOT EXISTS (8 张表)
      seed.js              # 种子 admin 用户
    middleware/
      auth.js              # JWT Bearer Token 校验
      admin.js             # 管理员权限检查
    routes/                # REST API 路由 (auth, groups, courses, students, templates, sendLogs, stats, settings, admin)
    utils/
      hash.js              # PBKDF2-SHA256 密码哈希 (兼容 Werkzeug 格式)
      weekday.js           # 星期常量

client/                    # Python Flask 客户端 (从原 app/ 拆分)
  run.py                   # 入口
  app/
    __init__.py            # create_app(): 注册蓝图 + context_processor 注入 current_user
    config.py              # SERVER_BASE_URL, AI_API_KEY, SECRET_KEY
    api_client.py          # HTTP 客户端封装 (对 Node.js API 的每个端点一个方法)
    middleware.py           # login_required / api_login_required / admin_required 装饰器
    routes/                # 所有路由 → SQLAlchemy 查询替换为 api_client 调用
    services/              # ai_generator, message_renderer, wechat_sender, screenshot
    templates/             # Jinja2 (不变)
    static/                # CSS/JS (不变)
```

## 启动与运行

```bash
# 1. 启动 Node.js 服务端
cd server && npm install && npm start
# → http://localhost:5001

# 2. 启动 Python 客户端
pip install -r requirements.txt
python3 run.py
# → 浏览器自动打开 http://127.0.0.1:5000
# 默认管理员: admin / admin123
```

## 技术栈

- **服务端**: Node.js + Express + better-sqlite3 (SQLite) + jsonwebtoken (JWT)
- **客户端**: Flask (模板渲染 + 路由) + requests (API 调用)
- **前端**: Bootstrap 5 + Jinja2 + htmx + vanilla JS
- **微信控制**: AppleScript (macOS) / pyautogui (Windows)
- **AI**: DeepSeek API (`deepseek-v4-flash`)，通过 `urllib` 直接调用

## 关键设计约定

- **认证**: 客户端 Flask 调用 Node.js `/api/auth/login` → 获得 JWT → 存入 `session['jwt']`。后续所有数据操作通过 `api_client.py` 自动附加 `Authorization: Bearer <jwt>` 头
- **API 登录检查**: `api_login_required` (middleware.py) 返回 JSON 401，`login_required` 返回 302。fetch 请求必须用前者
- **context_processor**: `__init__.py` 的 `inject_user()` 从 `session['teacher']` 创建代理对象，兼容模板中的 `{{ current_user.xxx }}`
- **AI 在线程内**: `_run_send_job` 后台线程通过传入 JWT 创建独立 ApiClient 实例调用 Node.js API
- **AI Key 全局**: 在 `config.py` 的 `AI_API_KEY` 配置
- **模板变量**: `{name}`, `{class}`, `{date}`, `{weekday}`, `{teacher}`, `{autocontent}`, `{performance}`, `{homework}`

## API 端点 (Node.js)

所有端点（除 login）需 `Authorization: Bearer <token>` 头。完整列表见 plan file。

## 密码哈希兼容

Node.js 使用 `crypto.pbkdf2Sync` (60万次迭代, SHA-256)，格式为 `pbkdf2:sha256:600000$salt_hex$hash_hex`，与 Python Werkzeug `generate_password_hash` 兼容。

## 批量发送流程

1. `/send` 页面选择模板 → 按需显示"课程概要"输入和每人"表现备注"输入
2. `startSend()` fetch POST → `/send/start`，携带 `template_id`, `student_ids[]`, `autocontent_description`, `performance_<id>`
3. 后端创建 `_jobs` 字典条目 → 启动后台线程 `_run_send_job()`
4. 线程：`generate_autocontent()` 一次 → 逐个学生：`generate_performance()` → `render_message()` → `send_message()`(AppleScript/pyautogui) → `capture_wechat_window()` 截图 → `api.create_send_log()` 上报 Node.js
5. 前端 `pollProgress()` 每 2s fetch `/send/status/<job_id>`，更新进度条
6. 全部完成后 `stitch_images()` 拼长图，前端显示下载按钮

## 常见问题

| 问题 | 原因 |
|------|------|
| fetch 报"会话已过期" | 路由用了 `@login_required` 而非 `@api_login_required`，或 fetch 没加 `credentials: 'same-origin'` |
| AI 在线程中返回"AI未配置" | `_get_ai_config()` 在当前线程无 Flask 上下文时 RuntimeError，需确保能 fallback 到 Config 类 |
| SSL 证书错误 | `_SSL_CONTEXT` 设为 `verify_mode=CERT_NONE` |
| 所有操作报"服务器连接失败" | Node.js 服务端未启动或 SERVER_BASE_URL 配置错误 |
| 登录后仍跳回登录页 | Node.js 服务端 JWT_SECRET 与服务端不匹配，或 session 过期 |
| 发送任务立即结束 / 无截图 | `_run_send_job` 线程内访问 `current_app`（如 `instance_path`），需通过参数传入。所有线程内依赖的 Flask 配置必须在启动线程前提取并传参 |
