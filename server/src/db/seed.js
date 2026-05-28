const db = require('./connection');
const { hashPassword } = require('../utils/hash');

function seedAdmin() {
  const existing = db.prepare('SELECT COUNT(*) as count FROM teachers').get();
  if (existing.count > 0) return;

  const passwordHash = hashPassword('admin123');
  db.prepare(`
    INSERT INTO teachers (username, password_hash, display_name, is_admin)
    VALUES (?, ?, ?, ?)
  `).run('admin', passwordHash, '管理员', 1);

  console.log('[初始化] 已创建默认管理员账号: admin / admin123，请尽快修改密码');
}

module.exports = { seedAdmin };
