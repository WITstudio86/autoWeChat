const crypto = require('crypto');

/**
 * Verify a password against a Werkzeug-format hash string.
 * Werkzeug format: pbkdf2:sha256:600000$salt_hex$hash_hex
 */
function verifyPassword(password, stored) {
  const parts = stored.split('$');
  if (parts.length !== 3) return false;

  const [algoPart, saltHex, hashHex] = parts;
  const algoParts = algoPart.split(':');
  if (algoParts.length < 3 || algoParts[0] !== 'pbkdf2') return false;

  const iterations = parseInt(algoParts[2], 10);
  const salt = Buffer.from(saltHex, 'hex');

  const derivedKey = crypto.pbkdf2Sync(password, salt, iterations, 32, 'sha256');
  return derivedKey.toString('hex') === hashHex;
}

/**
 * Generate a Werkzeug-compatible password hash.
 * Format: pbkdf2:sha256:600000$salt_hex$hash_hex
 */
function hashPassword(password) {
  const salt = crypto.randomBytes(16);
  const iterations = 600000;
  const derivedKey = crypto.pbkdf2Sync(password, salt, iterations, 32, 'sha256');
  return `pbkdf2:sha256:${iterations}$${salt.toString('hex')}$${derivedKey.toString('hex')}`;
}

module.exports = { verifyPassword, hashPassword };
