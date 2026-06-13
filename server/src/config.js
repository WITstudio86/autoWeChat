require('dotenv').config();

module.exports = {
  PORT: parseInt(process.env.PORT, 10) || 3004,
  JWT_SECRET: process.env.JWT_SECRET || 'autowechat-jwt-secret-change-in-production',
  DB_PATH: process.env.DB_PATH || './data/autowechat.db',
  JWT_EXPIRE_HOURS: parseInt(process.env.JWT_EXPIRE_HOURS, 10) || 72,
  AI_API_KEY: process.env.AI_API_KEY || '',
  AI_API_ENDPOINT: process.env.AI_API_ENDPOINT || 'https://api.deepseek.com/v1',
  AI_MODEL: process.env.AI_MODEL || 'deepseek-v4-flash',
};
