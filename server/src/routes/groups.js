const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const expireCheckMiddleware = require('../middleware/expireCheck');
const { sendJson, sendError } = require('../utils/response');
const { WEEKDAY_MAP } = require('../utils/weekday');

const router = express.Router();
router.use(authMiddleware);

function timeDisplay(row) {
  return `${row.day_of_week} ${row.start_time}-${row.end_time}`;
}

function groupWithCount(row) {
  const studentCnt = db.prepare('SELECT COUNT(*) as count FROM students WHERE course_group_id = ?').get(row.id);
  return { ...row, student_count: studentCnt.count, time_display: timeDisplay(row) };
}

// GET /api/groups
router.get('/', (req, res) => {
  const rows = db.prepare(
    'SELECT * FROM course_groups WHERE teacher_id = ? ORDER BY created_at DESC'
  ).all(req.teacherId);
  sendJson(res, rows.map(groupWithCount));
});

// POST /api/groups
router.post('/', expireCheckMiddleware, (req, res) => {
  const { name, day_of_week, start_time, end_time, weeks_ahead } = req.body;
  if (!name || !day_of_week || !start_time || !end_time) {
    return sendError(res, '所有字段不能为空');
  }
  if (!WEEKDAY_MAP.has(day_of_week)) {
    return sendError(res, '无效的星期');
  }

  // Check max_groups limit
  const teacher = db.prepare('SELECT max_groups FROM teachers WHERE id = ?').get(req.teacherId);
  if (teacher && teacher.max_groups) {
    const currentCount = db.prepare(
      'SELECT COUNT(*) as count FROM course_groups WHERE teacher_id = ?'
    ).get(req.teacherId);
    if (currentCount.count >= teacher.max_groups) {
      return sendError(res, `已达到班级数量上限（${teacher.max_groups}个）`, 403);
    }
  }

  const result = db.prepare(
    'INSERT INTO course_groups (teacher_id, name, day_of_week, start_time, end_time) VALUES (?,?,?,?,?)'
  ).run(req.teacherId, name.trim(), day_of_week, start_time, end_time);

  const gid = result.lastInsertRowid;

  const row = db.prepare('SELECT * FROM course_groups WHERE id = ?').get(gid);
  sendJson(res, groupWithCount(row), 201);
});

// GET /api/groups/:id
router.get('/:id', (req, res) => {
  const row = db.prepare(
    'SELECT * FROM course_groups WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '分组不存在', 404);
  sendJson(res, groupWithCount(row));
});

// PUT /api/groups/:id
router.put('/:id', expireCheckMiddleware, (req, res) => {
  const row = db.prepare(
    'SELECT * FROM course_groups WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '分组不存在', 404);

  const name = req.body.name || row.name;
  const dow = req.body.day_of_week || row.day_of_week;
  const start = req.body.start_time || row.start_time;
  const end = req.body.end_time || row.end_time;

  db.prepare(
    'UPDATE course_groups SET name=?, day_of_week=?, start_time=?, end_time=? WHERE id=?'
  ).run(name, dow, start, end, req.params.id);

  const updated = db.prepare('SELECT * FROM course_groups WHERE id = ?').get(req.params.id);
  sendJson(res, groupWithCount(updated));
});

// DELETE /api/groups/:id
router.delete('/:id', expireCheckMiddleware, (req, res) => {
  const row = db.prepare(
    'SELECT * FROM course_groups WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '分组不存在', 404);

  db.prepare('DELETE FROM course_groups WHERE id = ?').run(req.params.id);
  sendJson(res, { message: '已删除' });
});

module.exports = router;
