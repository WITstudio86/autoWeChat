from app.api_client import api


def generate_autocontent(description: str) -> str:
    """Generate course content via server-side AI."""
    if not description.strip():
        return "[未填写课程概要]"

    try:
        result = api.generate_autocontent(description)
        return result.get("content", "[AI 返回为空]")
    except Exception as e:
        return f"[AI生成失败: {str(e)}]"


def generate_performance(student_name: str, notes: str, course_context: str = "") -> str:
    """Generate personalized performance note via server-side AI."""
    if not notes.strip():
        return f"{student_name}本节课表现良好，继续加油！"

    try:
        result = api.generate_performance(student_name, notes, course_context)
        return result.get("content", "[AI 返回为空]")
    except Exception as e:
        return f"[AI生成失败: {str(e)}]"
