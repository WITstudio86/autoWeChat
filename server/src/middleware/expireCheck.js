const db = require('../db/connection');

function expireCheckMiddleware(req, res, next) {
  const teacher = db.prepare('SELECT expire_at FROM teachers WHERE id = ?').get(req.teacherId);
  if (!teacher) {
    return res.status(404).json({ error: '用户不存在' });
  }

  // NULL expire_at means permanent (admin accounts)
  if (teacher.expire_at === null || teacher.expire_at === undefined) {
    return next();
  }

  const now = new Date().toISOString();
  if (teacher.expire_at > now) {
    return next();
  }

  return res.status(403).json({ error: '账户已到期，仅支持查看数据，请联系管理员续期' });
}

module.exports = expireCheckMiddleware;
