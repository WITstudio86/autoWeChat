# autoWeChat 部署指南

## 项目说明

教培机构微信通知助手。分为三部分：

| 组件 | 说明 |
|------|------|
| **桌面客户端** (macOS / Windows) | 教师本地运行，通过 AppleScript/pyautogui 操控微信发送消息 |
| **云端服务端** (Linux) | Node.js + Express + SQLite，提供 REST API + JWT 认证 |
| **产品主页** | 静态页面，与服务端同域名，访问 `https://autowechat.你的域名.com/` |

---

## 构建流程

通过 GitHub Actions 统一构建：

```bash
git tag v1.0.0 && git push origin v1.0.0
```

CI 三平台并行构建（约 5-8 分钟），产物挂在 [GitHub Releases](https://github.com/WITstudio86/autoWeChat/releases)。

| 产物 | 用途 |
|------|------|
| `autoWeChat-macOS.zip` | macOS 客户端 |
| `autoWeChat-windows.zip` | Windows 客户端 |
| `autowechat-server-v*.tar.gz` | 服务端代码（部署用） |

---

## 服务端部署（全在 1Panel 完成）

### 1. 安装 Node.js 运行环境

1Panel → **工具箱** → **运行环境** → 安装 **Node.js 22.x**

### 2. 上传服务端代码

从 Release 下载 `autowechat-server-v*.tar.gz`，SSH 上传到服务器：

```bash
ssh root@<服务器IP> "mkdir -p /opt/autowechat/data"
scp autowechat-server-v*.tar.gz root@<服务器IP>:/opt/autowechat/
ssh root@<服务器IP> "
  cd /opt/autowechat &&
  tar -xzf autowechat-server-v*.tar.gz &&
  cp -r server/* . &&
  rm -rf server autowechat-server-v*.tar.gz
"
```

解压后结构：

```
/opt/autowechat/
├── src/
├── homepage/
├── package.json
└── data/
```

### 3. 配置环境变量

SSH 到服务器创建 `.env`：

```bash
cd /opt/autowechat

echo "JWT_SECRET=$(openssl rand -hex 64)" > .env

cat >> .env << 'EOF'
PORT=3004
JWT_EXPIRE_HOURS=72
AI_API_KEY=你的DeepSeek_API_Key
AI_API_ENDPOINT=https://api.deepseek.com/v1
AI_MODEL=deepseek-v4-flash
DB_PATH=./data/autowechat.db
EOF

# 编辑 .env，填入真实 API Key
```

### 4. 创建 Node.js 网站

1Panel → **网站** → **创建网站** → **运行环境**：

| 配置项 | 值 |
|--------|-----|
| 类型 | Node.js |
| 运行环境 | Node.js 22.x |
| 运行目录 | `/opt/autowechat` |
| 启动命令 | `npm start` |
| 包管理器 | npm |
| 应用端口 | `3004` |
| 外部映射 | `3004` |

### 5. 创建反向代理（绑定域名）

1Panel → **网站** → **创建网站** → **反向代理**：

| 配置项 | 值 |
|--------|-----|
| 主域名 | `autowechat.你的域名.com` |
| 代理地址 | `http://127.0.0.1:3004` |

创建后点进网站 → **配置** → **配置文件**，在 `location /` 块加：

```nginx
proxy_read_timeout 120s;
proxy_buffering off;
```

### 6. SSL 证书

网站 → **HTTPS** → 申请 Let's Encrypt 证书 → 开启 HTTPS，HTTP 选项选「禁止 HTTP」。

### 7. 验证

浏览器访问 `https://autowechat.你的域名.com/`，应该看到产品首页。

### 8. 数据库备份

1Panel → **计划任务** → 每天执行：

```bash
cp /opt/autowechat/data/autowechat.db /opt/backups/autowechat-$(date +%Y%m%d).db
find /opt/backups -name "autowechat-*.db" -mtime +7 -delete
```

---

## 客户端分发

从 Release 下载客户端 zip，上传到服务器下载目录：

```bash
scp autoWeChat-macOS.zip root@<服务器IP>:/opt/autowechat/homepage/download/
scp autoWeChat-windows.zip root@<服务器IP>:/opt/autowechat/homepage/download/
```

用户通过 `https://autowechat.你的域名.com/download/` 下载。

### macOS 首次运行

Gatekeeper 阻止未签名应用。用户打开 **系统设置 → 隐私与安全性**，找到提示点击「仍要打开」。或终端执行：

```bash
xattr -cr /Applications/autoWeChat.app
```

---

## 更新部署

1. GitHub Releases 下载新版本
2. SSH 解压覆盖，1Panel 面板重启网站：

```bash
scp autowechat-server-v*.tar.gz root@<服务器IP>:/opt/autowechat/
ssh root@<服务器IP> "
  cd /opt/autowechat &&
  tar -xzf autowechat-server-v*.tar.gz &&
  cp -r server/* . &&
  rm -rf server autowechat-server-v*.tar.gz &&
  npm install --production
"
```

3. 1Panel → 网站 → autoWeChat（Node.js）→ **重启**

---

## 附录：服务器目录结构

```
/opt/autowechat/
├── .env
├── package.json
├── src/
│   ├── index.js
│   ├── config.js
│   ├── db/
│   ├── middleware/
│   ├── routes/
│   └── utils/
├── homepage/
│   ├── index.html
│   ├── css/ js/ img/
│   └── download/
│       ├── autoWeChat-macOS.zip
│       └── autoWeChat-windows.zip
├── node_modules/
└── data/
    └── autowechat.db
```
