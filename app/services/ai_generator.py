import hashlib
import json
import ssl
import urllib.request
import urllib.error
from flask import current_app

# 跳过 SSL 证书验证（公司网络/代理环境常见问题）
_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

_cache = {}


def _get_ai_config():
    """Get AI config from Flask app config, with fallback to Config class."""
    try:
        key = current_app.config.get("AI_API_KEY", "")
        endpoint = current_app.config.get("AI_API_ENDPOINT", "https://api.deepseek.com/v1")
        model = current_app.config.get("AI_MODEL", "deepseek-v4-flash")
    except RuntimeError:
        from app.config import Config
        key = Config.AI_API_KEY
        endpoint = Config.AI_API_ENDPOINT
        model = Config.AI_MODEL
    return key, endpoint, model


def _call_llm(system_prompt: str, user_prompt: str,
              max_tokens: int = 400) -> str:
    """Call DeepSeek chat completions API."""
    api_key, api_endpoint, model = _get_ai_config()

    if not api_key or api_key == "你的DeepSeek-API-Key":
        return "[AI未配置，请在 app/config.py 中设置 AI_API_KEY]"

    cache_key = hashlib.md5(f"{system_prompt}:{user_prompt}:{model}".encode()).hexdigest()
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        url = f"{api_endpoint.rstrip('/')}/chat/completions"
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        })
        with urllib.request.urlopen(req, timeout=30, context=_SSL_CONTEXT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()
            _cache[cache_key] = content
            return content
    except Exception as e:
        return f"[AI生成失败: {str(e)}]"


def generate_autocontent(description: str) -> str:
    """Generate course content (~200 chars) from teacher's rough description."""
    if not description.strip():
        return "[未填写课程概要]"

    system_prompt = (
        "你是一位教培机构的助教，需要根据老师提供的课程概要，扩展成一段约200字的中文课程内容汇报，"
        "用于通过微信发送给家长。内容应包含：本节课学了什么、课堂情况、课后作业（如有）。"
        "语气亲切、专业、积极向上。直接输出内容，不要加任何前缀或后缀。"
    )

    return _call_llm(
        system_prompt=system_prompt,
        user_prompt=f"课程概要：{description}\n请扩展成约200字的课程内容汇报：",
        max_tokens=400,
    )


def generate_performance(student_name: str, notes: str) -> str:
    """Generate personalized performance note for a specific student."""
    if not notes.strip():
        return f"{student_name}本节课表现良好，继续加油！"

    system_prompt = (
        "你是一位教培机构的老师，需要根据对学生的简要备注，扩展成一段约80-100字的学生表现评语，"
        "用于通过微信发送给家长。评语应包含学生的课堂表现、进步点、需要改进的地方（如有）。"
        "语气温暖、真诚、有建设性。直接输出评语，不要加任何前缀或后缀。"
    )

    return _call_llm(
        system_prompt=system_prompt,
        user_prompt=f"学生姓名：{student_name}\n表现备注：{notes}\n请扩展成个性化的学生表现评语（约80-100字）：",
        max_tokens=250,
    )
