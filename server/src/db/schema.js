const db = require('./connection');

function createTables() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS teachers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      display_name TEXT,
      is_admin INTEGER DEFAULT 0,
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      teacher_id INTEGER NOT NULL,
      token TEXT NOT NULL UNIQUE,
      expires_at TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS course_groups (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      teacher_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      day_of_week INTEGER NOT NULL,
      start_time TEXT NOT NULL,
      end_time TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      course_group_id INTEGER NOT NULL,
      teacher_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      status TEXT DEFAULT 'upcoming',
      created_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (course_group_id) REFERENCES course_groups(id) ON DELETE CASCADE,
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS students (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      teacher_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      parent_wechat TEXT,
      course_group_id INTEGER,
      phone TEXT,
      notes TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
      FOREIGN KEY (course_group_id) REFERENCES course_groups(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS templates (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      teacher_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      content TEXT NOT NULL,
      description TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS send_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      teacher_id INTEGER NOT NULL,
      student_id INTEGER,
      template_id INTEGER,
      course_id INTEGER,
      message_content TEXT,
      status TEXT DEFAULT 'pending',
      error_message TEXT,
      screenshot_path TEXT,
      sent_at TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
      FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL,
      FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE SET NULL,
      FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS settings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      teacher_id INTEGER NOT NULL UNIQUE,
      ai_api_key TEXT,
      ai_endpoint TEXT DEFAULT 'https://api.openai.com/v1',
      ai_model TEXT DEFAULT 'gpt-4o-mini',
      wechat_delay_ms INTEGER DEFAULT 2500,
      target_app_name TEXT DEFAULT 'WeChat',
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ai_usage (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      teacher_id INTEGER NOT NULL,
      prompt_tokens INTEGER NOT NULL DEFAULT 0,
      completion_tokens INTEGER NOT NULL DEFAULT 0,
      total_tokens INTEGER NOT NULL DEFAULT 0,
      model TEXT NOT NULL DEFAULT '',
      purpose TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
    );
  `);

  // Migration: add columns that may not exist in older databases
  const migrations = [
    "ALTER TABLE settings ADD COLUMN target_app_name TEXT DEFAULT 'WeChat'",
    "ALTER TABLE teachers ADD COLUMN expire_at TEXT",
    "ALTER TABLE teachers ADD COLUMN max_groups INTEGER",
    "ALTER TABLE teachers ADD COLUMN max_students_per_group INTEGER",
  ];
  for (const sql of migrations) {
    try { db.exec(sql); } catch (_) { /* column already exists */ }
  }
}

module.exports = { createTables };
