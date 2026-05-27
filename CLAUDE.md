# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

教培机构微信通知助手。教师在 Web 页面管理课程分组、学员、通知模板，通过 AppleScript (macOS) / pyautogui (Windows) 自动化操控微信，批量向家长发送个性化通知。AI（DeepSeek）根据概要实时扩展课程内容和学员表现评语。

## 启动与运行

```bash
pip install -r requirements.txt
python3 run.py
# → 浏览器自动打开 http://127.0.0.1:5000
# 默认管理员: admin / admin123
```

`run.py` 在 `create_app()` 后 `threading.Timer(1, open_browser).start()` 自动打开浏览器。

## 技术栈

- **后端**: Flask + Flask-SQLAlchemy + Flask-Login
- **数据库**: SQLite (`instance/autowechat.db`)，首次运行时 `db.create_all()` + 种子 admin
- **前端**: Bootstrap 5 + Jinja2 + htmx（局部刷新/轮询）+ 少量 vanilla JS
- **AI**: DeepSeek API（`deepseek-v4-flash`），通过 `urllib` 直接调用（无 openai SDK）

## 架构

```
run.py                     # 入口，线程延迟 1s 开浏览器
app/
  __init__.py              # create_app() 工厂：注册蓝图、建表、种子 admin
  config.py                # 全局配置：DB 路径、AI Key/Endpoint/Model、Session
  extensions.py            # db, login_manager
  models/                  # SQLAlchemy 模型
  routes/                  # Flask 蓝图
  services/                # 业务逻辑（无 DB 依赖，可独立测试）
  templates/               # Jinja2 模板（按蓝图分目录）
  static/                  # CSS/JS/logo.png
local_server/              # 旧版原型（demo.py, local_serve.py），不再使用
```

### 关键设计约定

- **API 登录检查**：所有被 JS `fetch()` 调用的路由用 `@api_login_required`（自行实现，返回 JSON 401），不用 `@login_required`。`@login_required` 会 302 重定向到 /login，fetch 跟随重定向后拿到 HTML，前端 `safeJson()` 看到 HTML 就弹"会话已过期"。
- **AI 在线程内**：后台线程没有 Flask 上下文，AI 函数 `_get_ai_config()` 优先读 `current_app.config`，`RuntimeError` 时 fallback 到直接 import `Config` 类。
- **AI Key 全局**：DeepSeek Key 在 `config.py` 的 `AI_API_KEY`，教师无需在设置页配置。
- **模板变量**：`{name}`, `{class}`, `{date}`, `{weekday}`, `{teacher}`, `{autocontent}`, `{performance}`。后两个在发送时由用户填概要、AI 实时扩展。

### 数据库关系

- `CourseGroup.courses` → backref `group`（**不是** `course_group`）
- `CourseGroup.students` → backref `course_group`
- `Teacher.settings` → backref `settings`（`uselist=False`，一对一）

### 批量发送流程

1. `/send` 页面选择模板 → 按需显示"课程概要"输入和每人"表现备注"输入
2. `startSend()` fetch POST → `/send/start`，携带 `template_id`, `student_ids[]`, `autocontent_description`, `performance_<id>`
3. 后端主线读取 AI 配置(`current_app.config`)，传入后台线程
4. 线程：`generate_autocontent()` 一次 → 逐个学生：`generate_performance()` → `render_message()` → `send_message()`(AppleScript/pyautogui) → `SendLog`
5. 前端 `pollProgress()` 每 2s fetch `/send/status/<job_id>`，htmx 更新进度条

### 微信发送

`services/wechat_sender.py`：macOS 用 `osascript` 模拟 Cmd+F/Cmd+V/Enter，Windows 用 `pyautogui`。阻塞式，每次约 3-5 秒。

## 常见问题

| 问题 | 原因 |
|------|------|
| fetch 报"会话已过期" | 路由用了 `@login_required` 而非 `@api_login_required`，或 fetch 没加 `credentials: 'same-origin'` |
| `AttributeError: 'Course' object has no attribute 'course_group'` | 应写 `course.group`，backref 名是 `group` |
| AI 在线程中返回"AI未配置" | `_get_ai_config()` 在当前线程无 Flask 上下文时 RuntimeError，需确保能 fallback 到 Config 类 |
| SSL 证书错误 | `_SSL_CONTEXT` 设为 `verify_mode=CERT_NONE`，公司代理环境的常见问题 |
