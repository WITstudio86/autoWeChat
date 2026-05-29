const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const expireCheckMiddleware = require('../middleware/expireCheck');
const { sendJson, sendError } = require('../utils/response');

const router = express.Router();
router.use(authMiddleware);

// GET /api/templates
router.get('/', (req, res) => {
  const rows = db.prepare(
    'SELECT * FROM templates WHERE teacher_id = ? ORDER BY updated_at DESC'
  ).all(req.teacherId);
  sendJson(res, rows);
});

// POST /api/templates
router.post('/', expireCheckMiddleware, (req, res) => {
  const name = (req.body.name || '').trim();
  const content = (req.body.content || '').trim();
  if (!name || !content) return sendError(res, '模板名称和内容不能为空');

  const result = db.prepare(
    'INSERT INTO templates (teacher_id, name, content, description) VALUES (?,?,?,?)'
  ).run(req.teacherId, name, content, req.body.description || null);

  const row = db.prepare('SELECT * FROM templates WHERE id = ?').get(result.lastInsertRowid);
  sendJson(res, row, 201);
});

// GET /api/templates/:id
router.get('/:id', (req, res) => {
  const row = db.prepare(
    'SELECT * FROM templates WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '模板不存在', 404);
  sendJson(res, row);
});

// PUT /api/templates/:id
router.put('/:id', expireCheckMiddleware, (req, res) => {
  const row = db.prepare(
    'SELECT * FROM templates WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '模板不存在', 404);

  const name = 'name' in req.body ? (req.body.name || '').trim() : row.name;
  const content = 'content' in req.body ? (req.body.content || '').trim() : row.content;
  if (!name || !content) return sendError(res, '模板名称和内容不能为空');

  const desc = 'description' in req.body ? (req.body.description || null) : row.description;

  db.prepare(
    "UPDATE templates SET name=?, content=?, description=?, updated_at=datetime('now') WHERE id=?"
  ).run(name, content, desc, req.params.id);

  const updated = db.prepare('SELECT * FROM templates WHERE id = ?').get(req.params.id);
  sendJson(res, updated);
});

// DELETE /api/templates/:id
router.delete('/:id', expireCheckMiddleware, (req, res) => {
  const row = db.prepare(
    'SELECT * FROM templates WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '模板不存在', 404);

  db.prepare('DELETE FROM templates WHERE id = ?').run(req.params.id);
  sendJson(res, { message: '已删除' });
});

module.exports = router;
