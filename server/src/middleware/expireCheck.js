const db = require('../db/connection');

function expireCheckMiddleware(req, res, next) {
  const teacher = db.prepare(
    "SELECT expire_at FROM teachers WHERE id = ? AND (expire_at IS NULL OR datetime(expire_at) > datetime('now'))"
  ).get(req.teacherId);

  if (!teacher) {
    // Could be: user not found, or expire_at <= now
    // Check which case we're in
    const exists = db.prepare('SELECT id, expire_at FROM teachers WHERE id = ?').get(req.teacherId);
    if (!exists) {
      return res.status(404).json({ error: '用户不存在' });
    }
    return res.status(403).json({ error: '账户已到期，仅支持查看数据，请联系管理员续期' });
  }

  // expire_at IS NULL or expire_at > now — allow
  next();
}

module.exports = expireCheckMiddleware;
