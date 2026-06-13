const express = require('express');
const cors = require('cors');
const path = require('path');
const config = require('./config');
const { createTables } = require('./db/schema');
const { seedAdmin } = require('./db/seed');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Initialize database
createTables();
seedAdmin();

// Static homepage
const homepagePath = path.join(__dirname, '..', 'homepage');
app.use(express.static(homepagePath));

// SPA fallback: serve index.html for non-API routes
app.get(/^\/(?!api\/).*/, (req, res) => {
  const filePath = path.join(homepagePath, req.path === '/' ? 'index.html' : req.path);
  res.sendFile(filePath, { maxAge: 0 }, (err) => {
    if (err) {
      // Try index.html for client-side routing
      res.sendFile(path.join(homepagePath, 'index.html'));
    }
  });
});

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/groups', require('./routes/groups'));
app.use('/api/courses', require('./routes/courses'));
app.use('/api/students', require('./routes/students'));
app.use('/api/templates', require('./routes/templates'));
app.use('/api/send-logs', require('./routes/sendLogs'));
app.use('/api/stats', require('./routes/stats'));
app.use('/api/settings', require('./routes/settings'));
app.use('/api/admin', require('./routes/admin'));
app.use('/api/ai', require('./routes/ai'));

// 404
app.use((req, res) => {
  res.status(404).json({ error: 'Not Found' });
});

// Error handler
app.use((err, req, res, _next) => {
  console.error(err);
  res.status(500).json({ error: '服务器内部错误' });
});

app.listen(config.PORT, () => {
  console.log(`[服务端] 启动在 http://0.0.0.0:${config.PORT}`);
});
