const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const { sendJson } = require('../utils/response');

const router = express.Router();
router.use(authMiddleware);

function getOrCreateSettings(teacherId) {
  let row = db.prepare('SELECT * FROM settings WHERE teacher_id = ?').get(teacherId);
  if (!row) {
    db.prepare('INSERT INTO settings (teacher_id) VALUES (?)').run(teacherId);
    row = db.prepare('SELECT * FROM settings WHERE teacher_id = ?').get(teacherId);
  }
  return row;
}

// GET /api/settings
router.get('/', (req, res) => {
  sendJson(res, getOrCreateSettings(req.teacherId));
});

// PUT /api/settings
router.put('/', (req, res) => {
  getOrCreateSettings(req.teacherId);

  const allowedFields = ['ai_api_key', 'ai_endpoint', 'ai_model', 'wechat_delay_ms', 'target_app_name'];
  const updates = [];
  const values = [];

  for (const field of allowedFields) {
    if (field in req.body) {
      updates.push(`${field} = ?`);
      values.push(req.body[field]);
    }
  }

  if (updates.length > 0) {
    values.push(req.teacherId);
    db.prepare(`UPDATE settings SET ${updates.join(', ')} WHERE teacher_id = ?`).run(...values);
  }

  const row = db.prepare('SELECT * FROM settings WHERE teacher_id = ?').get(req.teacherId);
  sendJson(res, row);
});

module.exports = router;
