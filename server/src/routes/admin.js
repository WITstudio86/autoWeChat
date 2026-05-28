const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const adminMiddleware = require('../middleware/admin');
const { hashPassword } = require('../utils/hash');
const { sendJson, sendError } = require('../utils/response');

const router = express.Router();
router.use(authMiddleware);
router.use(adminMiddleware);

// GET /api/admin/teachers
router.get('/teachers', (req, res) => {
  const rows = db.prepare('SELECT * FROM teachers ORDER BY created_at DESC').all();
  const result = rows.map(r => {
    const { password_hash, ...t } = r;
    return t;
  });
  sendJson(res, result);
});

// POST /api/admin/teachers
router.post('/teachers', (req, res) => {
  const username = (req.body.username || '').trim();
  const password = req.body.password || '';
  if (!username || !password) return sendError(res, '用户名和密码不能为空');

  const existing = db.prepare('SELECT id FROM teachers WHERE username = ?').get(username);
  if (existing) return sendError(res, '用户名已存在', 409);

  const result = db.prepare(
    'INSERT INTO teachers (username, password_hash, display_name) VALUES (?,?,?)'
  ).run(username, hashPassword(password), req.body.display_name || null);

  const row = db.prepare('SELECT * FROM teachers WHERE id = ?').get(result.lastInsertRowid);
  const { password_hash, ...teacher } = row;
  sendJson(res, teacher, 201);
});

// PUT /api/admin/teachers/:id
router.put('/teachers/:id', (req, res) => {
  const row = db.prepare('SELECT * FROM teachers WHERE id = ?').get(req.params.id);
  if (!row) return sendError(res, '教师不存在', 404);

  const updates = [];
  const values = [];

  if ('display_name' in req.body) {
    updates.push('display_name = ?');
    values.push(req.body.display_name || null);
  }

  if ('is_active' in req.body) {
    if (row.is_admin && !req.body.is_active) {
      return sendError(res, '不能禁用管理员账号');
    }
    updates.push('is_active = ?');
    values.push(req.body.is_active ? 1 : 0);
  }

  if (updates.length > 0) {
    values.push(req.params.id);
    db.prepare(`UPDATE teachers SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  const updated = db.prepare('SELECT * FROM teachers WHERE id = ?').get(req.params.id);
  const { password_hash, ...teacher } = updated;
  sendJson(res, teacher);
});

// DELETE /api/admin/teachers/:id
router.delete('/teachers/:id', (req, res) => {
  const tid = parseInt(req.params.id, 10);
  if (req.teacherId === tid) return sendError(res, '不能删除自己的账号');

  const row = db.prepare('SELECT * FROM teachers WHERE id = ?').get(tid);
  if (!row) return sendError(res, '教师不存在', 404);

  db.prepare('DELETE FROM teachers WHERE id = ?').run(tid);
  sendJson(res, { message: '已删除' });
});

// POST /api/admin/teachers/:id/reset-password
router.post('/teachers/:id/reset-password', (req, res) => {
  const password = req.body.password || '';
  if (!password || password.length < 6) return sendError(res, '密码长度至少6位');

  const row = db.prepare('SELECT * FROM teachers WHERE id = ?').get(req.params.id);
  if (!row) return sendError(res, '教师不存在', 404);

  db.prepare('UPDATE teachers SET password_hash = ? WHERE id = ?')
    .run(hashPassword(password), req.params.id);

  sendJson(res, { message: '密码已重置' });
});

module.exports = router;
