require('dotenv').config();

module.exports = {
  PORT: parseInt(process.env.PORT, 10) || 5001,
  JWT_SECRET: process.env.JWT_SECRET || 'autowechat-jwt-secret-change-in-production',
  DB_PATH: process.env.DB_PATH || './data/autowechat.db',
  JWT_EXPIRE_HOURS: parseInt(process.env.JWT_EXPIRE_HOURS, 10) || 72,
};
