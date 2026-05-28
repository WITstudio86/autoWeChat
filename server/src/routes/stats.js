const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const { sendJson } = require('../utils/response');
const { WEEKDAY_OPTIONS } = require('../utils/weekday');

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

  const upcomingCourses = db.prepare(
    "SELECT * FROM courses WHERE teacher_id = ? AND status = 'upcoming' AND date >= ? AND date <= ? ORDER BY date LIMIT 10"
  ).all(tid, todayStr, weekEndStr);

  const todayCourses = db.prepare(
    'SELECT * FROM courses WHERE teacher_id = ? AND date = ?'
  ).all(tid, todayStr);

  const recentSends = db.prepare(
    'SELECT * FROM send_logs WHERE teacher_id = ? ORDER BY sent_at DESC LIMIT 5'
  ).all(tid);

  const monthlySends = db.prepare(
    'SELECT COUNT(*) as count FROM send_logs WHERE teacher_id = ? AND sent_at >= ?'
  ).get(tid, monthStartStr).count;

  function courseWithWeekday(r) {
    let wd = '';
    try {
      const d = new Date(r.date + 'T00:00:00');
      wd = WEEKDAY_OPTIONS[d.getDay() === 0 ? 6 : d.getDay() - 1];
    } catch { /* ignore */ }
    const group = db.prepare('SELECT name FROM course_groups WHERE id = ?').get(r.course_group_id);
    return { ...r, weekday_display: wd, group_name: group ? group.name : null };
  }

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
    upcoming_courses: upcomingCourses.map(courseWithWeekday),
    today_courses: todayCourses.map(courseWithWeekday),
    recent_sends: recentSends.map(logWithNames),
    monthly_sends: monthlySends,
  });
});

module.exports = router;
