const express = require('express');
const jwt = require('jsonwebtoken');
const db = require('../db/connection');
const config = require('../config');
const { verifyPassword } = require('../utils/hash');
const { sendJson, sendError } = require('../utils/response');
const authMiddleware = require('../middleware/auth');

const router = express.Router();

// POST /api/auth/login (public)
router.post('/login', (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return sendError(res, '用户名和密码不能为空');
  }

  const teacher = db.prepare('SELECT * FROM teachers WHERE username = ?').get(username.trim());
  if (!teacher || !verifyPassword(password, teacher.password_hash)) {
    return sendError(res, '用户名或密码错误', 401);
  }
  if (!teacher.is_active) {
    return sendError(res, '账号已被禁用', 403);
  }

  const token = jwt.sign(
    { teacher_id: teacher.id, is_admin: !!teacher.is_admin },
    config.JWT_SECRET,
    { expiresIn: `${config.JWT_EXPIRE_HOURS}h` }
  );

  const expiresAt = new Date(Date.now() + config.JWT_EXPIRE_HOURS * 3600 * 1000).toISOString();

  const { password_hash, ...teacherData } = teacher;
  sendJson(res, { token, expires_at: expiresAt, teacher: teacherData });
});

// POST /api/auth/logout (public - best effort)
router.post('/logout', (req, res) => {
  sendJson(res, { message: '已登出' });
});

// GET /api/auth/me (auth required)
router.get('/me', authMiddleware, (req, res) => {
  const teacher = db.prepare('SELECT * FROM teachers WHERE id = ?').get(req.teacherId);
  if (!teacher) {
    return sendError(res, '用户不存在', 404);
  }
  const { password_hash, ...teacherData } = teacher;
  sendJson(res, teacherData);
});

module.exports = router;
