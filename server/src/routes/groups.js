const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const { sendJson, sendError } = require('../utils/response');
const { WEEKDAY_OPTIONS, WEEKDAY_MAP } = require('../utils/weekday');

const router = express.Router();
router.use(authMiddleware);

function timeDisplay(row) {
  return `${row.day_of_week} ${row.start_time}-${row.end_time}`;
}

function groupWithCount(row) {
  const studentCnt = db.prepare('SELECT COUNT(*) as count FROM students WHERE course_group_id = ?').get(row.id);
  const courseCnt = db.prepare('SELECT COUNT(*) as count FROM courses WHERE course_group_id = ?').get(row.id);
  return { ...row, student_count: studentCnt.count, course_count: courseCnt.count, time_display: timeDisplay(row) };
}

// GET /api/groups
router.get('/', (req, res) => {
  const rows = db.prepare(
    'SELECT * FROM course_groups WHERE teacher_id = ? ORDER BY created_at DESC'
  ).all(req.teacherId);
  sendJson(res, rows.map(groupWithCount));
});

// POST /api/groups
router.post('/', (req, res) => {
  const { name, day_of_week, start_time, end_time, weeks_ahead } = req.body;
  if (!name || !day_of_week || !start_time || !end_time) {
    return sendError(res, '所有字段不能为空');
  }
  if (!WEEKDAY_MAP.has(day_of_week)) {
    return sendError(res, '无效的星期');
  }

  const result = db.prepare(
    'INSERT INTO course_groups (teacher_id, name, day_of_week, start_time, end_time) VALUES (?,?,?,?,?)'
  ).run(req.teacherId, name.trim(), day_of_week, start_time, end_time);

  const gid = result.lastInsertRowid;
  generateCourses(gid, req.teacherId, day_of_week, weeks_ahead || 8);

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
router.put('/:id', (req, res) => {
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
router.delete('/:id', (req, res) => {
  const row = db.prepare(
    'SELECT * FROM course_groups WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!row) return sendError(res, '分组不存在', 404);

  db.prepare('DELETE FROM course_groups WHERE id = ?').run(req.params.id);
  sendJson(res, { message: '已删除' });
});

// GET /api/groups/:gid/courses
router.get('/:gid/courses', (req, res) => {
  const rows = db.prepare(
    'SELECT * FROM courses WHERE course_group_id = ? AND teacher_id = ? ORDER BY date'
  ).all(req.params.gid, req.teacherId);

  sendJson(res, rows.map(r => {
    const group = db.prepare('SELECT name FROM course_groups WHERE id = ?').get(r.course_group_id);
    return { ...r, weekday_display: weekdayDisplay(r.date), group_name: group ? group.name : null };
  }));
});

// POST /api/groups/:gid/courses/generate
router.post('/:gid/courses/generate', (req, res) => {
  const group = db.prepare(
    'SELECT * FROM course_groups WHERE id = ? AND teacher_id = ?'
  ).get(req.params.gid, req.teacherId);
  if (!group) return sendError(res, '分组不存在', 404);

  const weeks = req.body.weeks || 4;
  const newCourses = generateCourses(group.id, req.teacherId, group.day_of_week, weeks);

  sendJson(res, newCourses.map(r => ({ ...r, weekday_display: weekdayDisplay(r.date) })), 201);
});

// ── helpers ──

function weekdayDisplay(dateStr) {
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return WEEKDAY_OPTIONS[d.getDay() === 0 ? 6 : d.getDay() - 1];
  } catch {
    return '';
  }
}

function generateCourses(groupId, teacherId, dayOfWeek, weeksAhead) {
  const targetWd = WEEKDAY_MAP.get(dayOfWeek);
  if (targetWd === undefined) return [];

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayDow = today.getDay() === 0 ? 6 : today.getDay() - 1;

  let daysUntil = (targetWd - todayDow + 7) % 7;
  let nextDate = new Date(today);
  nextDate.setDate(today.getDate() + daysUntil);

  const newCourses = [];

  for (let i = 0; i < weeksAhead; i++) {
    if (nextDate >= today) {
      const dateStr = nextDate.toISOString().slice(0, 10);
      const existing = db.prepare(
        'SELECT id FROM courses WHERE course_group_id = ? AND date = ?'
      ).get(groupId, dateStr);

      if (!existing) {
        const result = db.prepare(
          'INSERT INTO courses (course_group_id, teacher_id, date, status) VALUES (?,?,?,?)'
        ).run(groupId, teacherId, dateStr, 'upcoming');

        const row = db.prepare('SELECT * FROM courses WHERE id = ?').get(result.lastInsertRowid);
        newCourses.push(row);
      }
    }
    nextDate.setDate(nextDate.getDate() + 7);
  }

  return newCourses;
}

module.exports = router;
