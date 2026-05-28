const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const { sendJson, sendError } = require('../utils/response');

const router = express.Router();
router.use(authMiddleware);

// GET /api/students
router.get('/', (req, res) => {
  const { group_id, sort, filter } = req.query;

  let sql = 'SELECT s.* FROM students s WHERE s.teacher_id = ?';
  const params = [req.teacherId];

  if (group_id !== undefined && group_id !== '') {
    if (group_id === '-1') {
      sql += ' AND s.course_group_id IS NULL';
    } else {
      sql += ' AND s.course_group_id = ?';
      params.push(parseInt(group_id, 10));
    }
  }

  if (filter) {
    sql += ' AND s.name LIKE ?';
    params.push(`%${filter}%`);
  }

  if (sort === 'time') {
    sql += ' LEFT JOIN course_groups g ON s.course_group_id = g.id ORDER BY g.day_of_week, g.start_time, s.name';
  } else {
    sql += ' ORDER BY s.name';
  }

  const rows = db.prepare(sql).all(...params);
  const result = rows.map(r => {
    const g = r.course_group_id
      ? db.prepare('SELECT name, day_of_week, start_time, end_time FROM course_groups WHERE id = ?').get(r.course_group_id)
      : null;
    return {
      ...r,
      group_name: g ? g.name : null,
      group_time_display: g ? `${g.day_of_week} ${g.start_time}-${g.end_time}` : null,
    };
  });
  sendJson(res, result);
});

// POST /api/students
router.post('/', (req, res) => {
  const name = (req.body.name || '').trim();
  if (!name) return sendError(res, '学员姓名不能为空');

  const result = db.prepare(
    'INSERT INTO students (teacher_id, name, parent_wechat, course_group_id, phone, notes) VALUES (?,?,?,?,?,?)'
  ).run(
    req.teacherId,
    name,
    req.body.parent_wechat || null,
    req.body.course_group_id || null,
    req.body.phone || null,
    req.body.notes || null
  );

  const row = db.prepare('SELECT * FROM students WHERE id = ?').get(result.lastInsertRowid);
  sendJson(res, row, 201);
});

// GET /api/students/:id
router.get('/:id', (req, res) => {
  const row = db.prepare(
    'SELECT * FROM students WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '学员不存在', 404);
  sendJson(res, row);
});

// PUT /api/students/:id
router.put('/:id', (req, res) => {
  const row = db.prepare(
    'SELECT * FROM students WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '学员不存在', 404);

  const name = 'name' in req.body ? (req.body.name || '').trim() : row.name;
  if (!name) return sendError(res, '学员姓名不能为空');

  db.prepare(
    'UPDATE students SET name=?, parent_wechat=?, course_group_id=?, phone=?, notes=? WHERE id=?'
  ).run(
    name,
    'parent_wechat' in req.body ? (req.body.parent_wechat || null) : row.parent_wechat,
    'course_group_id' in req.body ? (req.body.course_group_id || null) : row.course_group_id,
    'phone' in req.body ? (req.body.phone || null) : row.phone,
    'notes' in req.body ? (req.body.notes || null) : row.notes,
    req.params.id
  );

  const updated = db.prepare('SELECT * FROM students WHERE id = ?').get(req.params.id);
  sendJson(res, updated);
});

// DELETE /api/students/:id
router.delete('/:id', (req, res) => {
  const row = db.prepare(
    'SELECT * FROM students WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '学员不存在', 404);

  db.prepare('DELETE FROM students WHERE id = ?').run(req.params.id);
  sendJson(res, { message: '已删除' });
});

// POST /api/students/:id/move
router.post('/:id/move', (req, res) => {
  const row = db.prepare(
    'SELECT * FROM students WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '学员不存在', 404);

  db.prepare('UPDATE students SET course_group_id = ? WHERE id = ?')
    .run(req.body.course_group_id || null, req.params.id);

  const updated = db.prepare('SELECT * FROM students WHERE id = ?').get(req.params.id);
  sendJson(res, updated);
});

module.exports = router;
