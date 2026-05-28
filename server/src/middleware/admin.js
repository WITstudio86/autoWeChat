function adminMiddleware(req, res, next) {
  if (!req.isAdmin) {
    return res.status(403).json({ error: '需要管理员权限' });
  }
  next();
}

module.exports = adminMiddleware;
