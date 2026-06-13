# autoWeChat 部署指南

## 项目说明

教培机构微信通知助手。分为三部分：

| 组件 | 说明 |
|------|------|
| **桌面客户端** (macOS / Windows) | Python Flask + PyInstaller，通过 AppleScript/pyautogui 操控微信 |
| **云端服务端** (Linux) | Node.js + Express + SQLite，提供 REST API + JWT 认证 |
| **产品主页** | 静态页面，通过子域名 `https://autowechat.你的域名.com/` 访问 |

---

## 构建流程

通过 GitHub Actions 统一构建，**本地无需手动编译**。

### 触发构建

```bash
git tag v1.0.0 && git push origin v1.0.0
```

CI 自动三平台并行构建（约 5-8 分钟），产物挂在 [GitHub Releases](https://github.com/WITstudio86/autoWeChat/releases) 页面。

### 产物说明

| 产物 | 用途 |
|------|------|
| `autoWeChat-macOS.zip` | macOS 客户端，解压即用 |
| `autoWeChat-windows.zip` | Windows 客户端，解压即用 |
| `autowechat-server-v*.tar.gz` | 服务端代码（不含 node_modules） |

### 手动本地构建（可选）

```bash
# macOS 客户端
pip install -r requirements.txt pyinstaller
pyinstaller autoWeChat.spec
# 产物在 dist/autoWeChat.app → 压缩为 autoWeChat-macOS.zip

# 服务端打包
tar -czf autowechat-server.tar.gz --exclude='server/node_modules' --exclude='server/.env' --exclude='server/data' server/
```

---

## 服务端部署

### 1. DNS 配置

在域名 DNS 管理后台添加 A 记录：

| 主机记录 | 记录类型 | 记录值 |
|---------|---------|--------|
| `autowechat` | A | `<服务器公网IP>` |

### 2. 上传并部署

从 Release 页面下载 `autowechat-server-v*.tar.gz`，上传到服务器：

```bash
# 首次部署 → 创建目录
ssh root@<服务器IP> "mkdir -p /opt/autowechat/data"

# 上传并解压
scp autowechat-server-v*.tar.gz root@<服务器IP>:/opt/autowechat/
ssh root@<服务器IP> "cd /opt/autowechat && tar -xzf autowechat-server-v*.tar.gz && cp -r server/* . && rm -rf server autowechat-server-v*.tar.gz"
```

### 3. 配置环境变量

```bash
cd /opt/autowechat

# 生成 JWT 密钥
echo "JWT_SECRET=$(openssl rand -hex 64)" > .env

# 追加其他配置
cat >> .env << 'EOF'
PORT=5001
JWT_EXPIRE_HOURS=72
AI_API_KEY=你的DeepSeek_API_Key
AI_API_ENDPOINT=https://api.deepseek.com/v1
AI_MODEL=deepseek-v4-flash
DB_PATH=/opt/autowechat/data/autowechat.db
EOF
```

编辑 `.env`，填入真实的 DeepSeek API Key。

### 4. 安装依赖并启动

```bash
cd /opt/autowechat
npm install --production

# PM2 守护进程（1Panel 已自带 PM2）
pm2 start src/index.js --name autowechat
pm2 save
pm2 startup
```

验证：

```bash
curl http://127.0.0.1:5001/                          # 产品首页
curl http://127.0.0.1:5001/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'    # API 登录
```

### 5. OpenResty 反向代理

1Panel → **「网站」** → **「创建网站」** → **「反向代理」**：

| 配置项 | 值 |
|--------|-----|
| 主域名 | `autowechat.你的域名.com` |
| 代理地址 | `127.0.0.1:5001` |

创建后点击网站 → **「配置」** → **「配置文件」**，在 `location /` 块中加入：

```nginx
proxy_read_timeout 120s;
proxy_buffering off;
```

> AI 生成内容耗时较长，120s 超时必须设置。

### 6. SSL 证书

1. 网站 → **「HTTPS」** → **「申请证书」**：Let's Encrypt / HTTP 验证 / 自动续签开启
2. 申请成功后 **「启用 HTTPS」**，HTTP 选项选 **「禁止 HTTP」**

### 7. 更新部署

```bash
# 1. 从 Release 下载新版本 autowechat-server-v*.tar.gz
scp autowechat-server-v*.tar.gz root@<服务器IP>:/opt/autowechat/

# 2. 解压覆盖
ssh root@<服务器IP> "
  cd /opt/autowechat &&
  pm2 stop autowechat &&
  tar -xzf autowechat-server-v*.tar.gz &&
  cp -r server/src/* src/ &&
  rm -rf server autowechat-server-v*.tar.gz &&
  npm install --production &&
  pm2 start autowechat
"
```

### 8. 数据库备份

```bash
#!/bin/bash
cp /opt/autowechat/data/autowechat.db /opt/backups/autowechat-$(date +%Y%m%d).db
find /opt/backups -name "autowechat-*.db" -mtime +7 -delete
```

在 1Panel → **「计划任务」** 中添加，每天执行。

---

## 客户端分发

从 Release 页面下载客户端 zip，上传到服务器 `homepage/download/` 目录：

```bash
scp autoWeChat-macOS.zip root@<服务器IP>:/opt/autowechat/homepage/download/
scp autoWeChat-windows.zip root@<服务器IP>:/opt/autowechat/homepage/download/
```

用户通过 `https://autowechat.你的域名.com/download/` 下载。

### macOS 客户端首次运行

macOS Gatekeeper 会阻止未签名应用。用户需执行：

1. 下载 `autoWeChat-macOS.zip` 并解压
2. 打开 **系统设置 → 隐私与安全性**
3. 找到 `autoWeChat.app` 的阻塞提示，点击 **「仍要打开」**

或终端执行：

```bash
xattr -cr /Applications/autoWeChat.app
```

---

## 附录：服务端目录结构

```
/opt/autowechat/
├── .env
├── package.json
├── package-lock.json
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
├── data/
│   └── autowechat.db
└── node_modules/
```
