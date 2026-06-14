import traceback
from app.api_client import api


def generate_autocontent(description: str) -> str:
    """Generate course content via server-side AI."""
    if not description.strip():
        return "[未填写课程概要]"

    try:
        result = api.generate_autocontent(description)
        content = result.get("content", "")
        if not content:
            print("[AI] 课程内容生成返回为空")
            return "[AI 生成失败，请重试]"
        return content
    except Exception:
        print(f"[AI] 课程内容生成异常:\n{traceback.format_exc()}")
        return "[AI 生成失败，请检查服务端 AI 配置]"


def generate_performance(student_name: str, notes: str, course_context: str = "") -> str:
    """Generate personalized performance note via server-side AI."""
    if not notes.strip():
        return f"{student_name}本节课表现不错，继续加油！"

    try:
        result = api.generate_performance(student_name, notes, course_context)
        content = result.get("content", "")
        if not content:
            print(f"[AI] {student_name} 表现评语生成返回为空")
            return f"{student_name}本节课表现不错，继续加油！"
        return content
    except Exception:
        print(f"[AI] {student_name} 表现评语生成异常:\n{traceback.format_exc()}")
        return f"{student_name}本节课表现不错，继续加油！"
