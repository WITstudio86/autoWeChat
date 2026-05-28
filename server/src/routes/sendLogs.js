const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const { sendJson, sendError } = require('../utils/response');

const router = express.Router();
router.use(authMiddleware);

// POST /api/send-logs
router.post('/', (req, res) => {
  const { student_id, template_id } = req.body;
  if (!student_id || !template_id) {
    return sendError(res, '缺少字段: student_id, template_id');
  }

  const result = db.prepare(
    `INSERT INTO send_logs (teacher_id, student_id, template_id, course_id,
     message_content, status, error_message, screenshot_path)
     VALUES (?,?,?,?,?,?,?,?)`
  ).run(
    req.teacherId,
    student_id,
    template_id,
    req.body.course_id || null,
    req.body.message_content || '',
    req.body.status || 'success',
    req.body.error_message || null,
    req.body.screenshot_path || null
  );

  const row = db.prepare('SELECT * FROM send_logs WHERE id = ?').get(result.lastInsertRowid);
  const student = db.prepare('SELECT name FROM students WHERE id = ?').get(row.student_id);
  const template = db.prepare('SELECT name FROM templates WHERE id = ?').get(row.template_id);

  sendJson(res, {
    ...row,
    student_name: student ? student.name : null,
    template_name: template ? template.name : null,
  }, 201);
});

// GET /api/send-logs
router.get('/', (req, res) => {
  const limit = parseInt(req.query.limit, 10) || 100;

  const rows = db.prepare(
    'SELECT * FROM send_logs WHERE teacher_id = ? ORDER BY sent_at DESC LIMIT ?'
  ).all(req.teacherId, limit);

  const result = rows.map(r => {
    const student = db.prepare('SELECT name FROM students WHERE id = ?').get(r.student_id);
    const template = db.prepare('SELECT name FROM templates WHERE id = ?').get(r.template_id);
    return {
      ...r,
      student_name: student ? student.name : null,
      template_name: template ? template.name : null,
    };
  });

  sendJson(res, result);
});

module.exports = router;
