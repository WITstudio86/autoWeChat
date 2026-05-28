AVAILABLE_VARIABLES = {
    "{name}": "学员姓名",
    "{class}": "课程时间（如 周六 8:40-10:10）",
    "{date}": "上课日期（如 2026-05-27）",
    "{weekday}": "中文星期（周一~周日）",
    "{teacher}": "教师姓名",
    "{autocontent}": "课程内容（发送时填写概要，AI 扩展成约200字）",
    "{performance}": "学员表现（发送时填写每个学员的概要，AI 扩展成个性化评语）",
}


def render_message(
    template_content: str,
    student_name: str = "",
    course_time: str = "",
    course_date: str = "",
    weekday: str = "",
    teacher_name: str = "",
    autocontent: str = "",
    performance: str = "",
    **extra,
) -> str:
    """Replace template variables with actual values."""
    result = template_content
    replacements = {
        "{name}": student_name,
        "{class}": course_time,
        "{date}": course_date,
        "{weekday}": weekday,
        "{teacher}": teacher_name,
        "{autocontent}": autocontent or "[发送时填写课程概要自动生成]",
        "{performance}": performance or "[发送时填写表现概要自动生成]",
    }
    for var, val in replacements.items():
        result = result.replace(var, val)
    return result


def preview_message(template_content: str) -> str:
    """Preview template with sample data."""
    return render_message(
        template_content=template_content,
        student_name="张三",
        course_time="周六 8:40-10:10",
        course_date="2026-05-30",
        weekday="周六",
        teacher_name="李老师",
        autocontent="本节课我们学习了分数的基本运算，包括通分、约分和加减法。同学们表现积极，张三在课堂上回答问题非常踊跃。课后请完成练习册第25页的习题。",
        performance="张三本节课表现优秀，积极回答问题，作业完成情况良好，继续保持！",
    )
