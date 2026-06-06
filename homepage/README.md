# autoWeChat Homepage

产品介绍页 / 下载页。纯静态文件，由 nginx 直接 serve。

## 目录结构

```
homepage/
  index.html          # 主页面
  css/style.css       # 自定义样式
  js/main.js          # 交互逻辑
  img/logo.png        # Logo
  download/           # 下载文件目录（用户自行放入）
```

## 部署（阿里云 + 1Panel + Docker）

### 1. 上传文件

将整个 `homepage/` 目录上传到服务器，例如 `/opt/autowechat/homepage/`。

### 2. nginx 配置

在 1Panel 中创建网站，配置如下：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 静态介绍页
    location / {
        root /opt/autowechat/homepage;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # 下载文件
    location /download/ {
        alias /opt/autowechat/homepage/download/;
    }

    # Flask 应用
    location /app/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Node.js API
    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 1Panel 操作

1. 创建「静态站点」：网站目录指向 `/opt/autowechat/homepage`
2. 添加「反向代理」规则：
   - 路径 `/app` → 目标 `http://127.0.0.1:5000`
   - 路径 `/api` → 目标 `http://127.0.0.1:5001`
3. 如需 HTTPS：在 1Panel 中申请/配置 SSL 证书

### 4. 放入下载文件

将编译好的客户端放入 `homepage/download/`：

```
homepage/download/
  autoWeChat.app           # macOS 应用
  autoWeChat-setup.exe     # Windows 安装包
```

文件名与 `index.html` 中的下载链接一致即可。前端 JS 会自动检测文件存在性，文件就位后「即将发布」徽章自动消失。

## 本地预览

直接在浏览器中打开 `homepage/index.html` 即可预览。CDN 依赖需要网络连接。
