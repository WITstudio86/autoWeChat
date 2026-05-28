const jwt = require('jsonwebtoken');
const config = require('../config');

function authMiddleware(req, res, next) {
  const header = req.headers.authorization;
  if (!header || !header.startsWith('Bearer ')) {
    return res.status(401).json({ error: '未登录或会话已过期，请重新登录' });
  }

  const token = header.slice(7);
  try {
    const payload = jwt.verify(token, config.JWT_SECRET);
    req.teacherId = payload.teacher_id;
    req.isAdmin = payload.is_admin;
    req.token = token;
    next();
  } catch (err) {
    return res.status(401).json({ error: '令牌已过期，请重新登录' });
  }
}

module.exports = authMiddleware;
