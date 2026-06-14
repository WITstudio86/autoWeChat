const https = require('https');
const config = require('../config');
const db = require('../db/connection');
const { sendJson, sendError } = require('../utils/response');
const authMiddleware = require('../middleware/auth');

const router = require('express').Router();

router.use(authMiddleware);

function callDeepSeek(systemPrompt, userPrompt, maxTokens) {
  return new Promise((resolve, reject) => {
    try {
      if (!config.AI_API_KEY) {
        return reject(new Error('AI API Key 未配置，请在服务端 .env 中设置 AI_API_KEY'));
      }

      const body = JSON.stringify({
        model: config.AI_MODEL,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        max_tokens: maxTokens,
        temperature: 0.7,
      });

      const endpoint = (config.AI_API_ENDPOINT || 'https://api.deepseek.com/v1').replace(/\/$/, '');
      const url = new URL(endpoint + '/chat/completions');
      const options = {
        hostname: url.hostname,
        port: url.port || 443,
        path: url.pathname + url.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${config.AI_API_KEY}`,
          'Content-Length': Buffer.byteLength(body),
        },
        timeout: 60000,
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices?.[0]?.message?.content?.trim();
            const usage = parsed.usage || null;
            if (content) {
              resolve({ content, usage });
            } else {
              reject(new Error(parsed.error?.message || 'AI 返回内容为空'));
            }
          } catch (e) {
            reject(new Error(`AI 响应解析失败: ${e.message}`));
          }
        });
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('AI 请求超时'));
      });

      req.on('error', (e) => {
        reject(new Error(`AI 请求失败: ${e.message}`));
      });

      req.write(body);
      req.end();
    } catch (e) {
      reject(new Error(`AI 请求构造失败: ${e.message}`));
    }
  });
}

function logUsage(teacherId, usage, purpose) {
  if (!usage) return;
  try {
    db.prepare(
      `INSERT INTO ai_usage (teacher_id, prompt_tokens, completion_tokens, total_tokens, model, purpose)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).run(teacherId, usage.prompt_tokens || 0, usage.completion_tokens || 0,
      usage.total_tokens || 0, config.AI_MODEL, purpose);
  } catch (_) { /* 非关键，静默失败 */ }
}

// POST /api/ai/autocontent
router.post('/autocontent', async (req, res) => {
  try {
    const { description } = req.body;

    if (!description || !description.trim()) {
      return sendJson(res, { content: '[未填写课程概要]' });
    }

    const systemPrompt =
      '你是一位教培机构的助教，需要根据老师提供的课程概要，扩展成一段约200字的中文课程内容汇报，' +
      '用于一对一发送给某位学生的家长。' +
      '内容应包含：本节课学了哪些具体知识点、用了什么教学方法或练习形式。' +
      '语气亲切、专业、积极向上。' +
      '重要规则：' +
      '1. 只描述课程本身的内容和教学安排，不要提及任何学生的课堂表现、状态或行为；' +
      '2. 不要出现「孩子们」「同学们」「大家」等群体性称呼，用「本节课学习了/讲解了/练习了」等客观表述；' +
      '3. 不要加任何称呼（如「亲爱的家长」）、问候语、落款、日期、署名；' +
      '4. 直接输出内容，不要加任何前缀或后缀。' +
      '5. 不要提及课后作业、练习或任何需要课后完成的内容；';

    const { content, usage } = await callDeepSeek(systemPrompt, `课程概要：${description}\n请扩展成约200字的课程内容汇报：`, 400);
    logUsage(req.teacherId, usage, 'autocontent');
    sendJson(res, { content });
  } catch (err) {
    console.error('[AI autocontent]', err.message);
    sendError(res, `AI 生成失败: ${err.message}`, 502);
  }
});

// POST /api/ai/performance
router.post('/performance', async (req, res) => {
  try {
    const { student_name, notes, course_context } = req.body;

    if (!student_name) {
      return sendError(res, '缺少学生姓名', 400);
    }

    if (!notes || !notes.trim()) {
      return sendJson(res, { content: `${student_name}本节课表现不错，继续加油！` });
    }

    let contextHint = '';
    if (course_context && course_context.trim()) {
      contextHint =
        `本节课的课程内容是：${course_context.trim()}。` +
        `请确保评语中的具体描述与这门课的内容相关，` +
        `不要出现与该课程类型无关的描述` +
        `（例如编程课不要说「书写工整」，美术课不要说「逻辑思维强」）。`;
    }

    const systemPrompt =
      '你是一位教培机构的老师，需要根据对学生的简要备注，扩展成一段约80-100字的学生个人表现评语，' +
      '用于一对一发送给该学生的家长。' +
      '评语应包含：该学生的课堂参与度、对知识点的掌握情况、进步或亮点、需要加强的地方（如有）。' +
      '语气温暖、真诚、有建设性。' +
      '重要规则：' +
      '1. 只针对该学生个人的表现，不要提及任何其他学生；' +
      '2. 表扬和批评必须贴合课程实际内容，不要出现与该课程类型无关的夸奖' +
      '   （如编程课不要夸「字迹工整」,体育课不要夸「做题认真」）；' +
      '3. 直接输出评语，不要加任何称呼、问候语、前缀或后缀。';

    const userPrompt =
      `学生姓名：${student_name}\n` +
      `表现备注：${notes}\n` +
      `${contextHint}` +
      `请扩展成个性化的学生表现评语（约80-100字）：`;

    const { content, usage } = await callDeepSeek(systemPrompt, userPrompt, 250);
    logUsage(req.teacherId, usage, 'performance');
    sendJson(res, { content });
  } catch (err) {
    console.error('[AI performance]', err.message);
    sendError(res, `AI 生成失败: ${err.message}`, 502);
  }
});

module.exports = router;
