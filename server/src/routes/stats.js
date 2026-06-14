const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const { sendJson } = require('../utils/response');

const router = express.Router();
router.use(authMiddleware);

// GET /api/stats
router.get('/', (req, res) => {
  const tid = req.teacherId;
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);

  const weekEnd = new Date(today);
  weekEnd.setDate(weekEnd.getDate() + 7);
  const weekEndStr = weekEnd.toISOString().slice(0, 10);

  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
  const monthStartStr = monthStart.toISOString().slice(0, 10);

  const studentCount = db.prepare('SELECT COUNT(*) as count FROM students WHERE teacher_id = ?').get(tid).count;
  const groupCount = db.prepare('SELECT COUNT(*) as count FROM course_groups WHERE teacher_id = ?').get(tid).count;
  const templateCount = db.prepare('SELECT COUNT(*) as count FROM templates WHERE teacher_id = ?').get(tid).count;

  const recentSends = db.prepare(
    'SELECT * FROM send_logs WHERE teacher_id = ? ORDER BY sent_at DESC LIMIT 5'
  ).all(tid);

  const monthlySends = db.prepare(
    'SELECT COUNT(*) as count FROM send_logs WHERE teacher_id = ? AND sent_at >= ?'
  ).get(tid, monthStartStr).count;

  function logWithNames(r) {
    const student = db.prepare('SELECT name FROM students WHERE id = ?').get(r.student_id);
    const template = db.prepare('SELECT name FROM templates WHERE id = ?').get(r.template_id);
    return {
      ...r,
      student_name: student ? student.name : null,
      template_name: template ? template.name : null,
    };
  }

  sendJson(res, {
    student_count: studentCount,
    group_count: groupCount,
    template_count: templateCount,
    recent_sends: recentSends.map(logWithNames),
    monthly_sends: monthlySends,
  });
});

module.exports = router;
