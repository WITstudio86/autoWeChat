const express = require('express');
const db = require('../db/connection');
const authMiddleware = require('../middleware/auth');
const { sendJson, sendError } = require('../utils/response');
const { WEEKDAY_OPTIONS } = require('../utils/weekday');

const router = express.Router();
router.use(authMiddleware);

// PUT /api/courses/:id/status
router.put('/:id/status', (req, res) => {
  const course = db.prepare(
    'SELECT * FROM courses WHERE id = ? AND teacher_id = ?'
  ).get(req.params.id, req.teacherId);
  if (!course) return sendError(res, '课程不存在', 404);

  const { status } = req.body;
  if (!['upcoming', 'completed', 'cancelled'].includes(status)) {
    return sendError(res, '无效的状态');
  }

  db.prepare('UPDATE courses SET status = ? WHERE id = ?').run(status, req.params.id);

  const row = db.prepare('SELECT * FROM courses WHERE id = ?').get(req.params.id);
  sendJson(res, { ...row, weekday_display: weekdayDisplay(row.date) });
});

function weekdayDisplay(dateStr) {
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return WEEKDAY_OPTIONS[d.getDay() === 0 ? 6 : d.getDay() - 1];
  } catch {
    return '';
  }
}

module.exports = router;
