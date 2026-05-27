from datetime import date, timedelta
from app.models.course import Course


WEEKDAY_MAP = {
    "周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6,
}


def generate_courses(group, weeks_ahead=8):
    """Generate Course instances for the given CourseGroup for the next N weeks."""
    target_weekday = WEEKDAY_MAP.get(group.day_of_week)
    if target_weekday is None:
        raise ValueError(f"无效的星期: {group.day_of_week}")

    today = date.today()
    days_until = (target_weekday - today.weekday()) % 7
    if days_until == 0:
        days_until = 0

    new_courses = []
    next_date = today + timedelta(days=days_until)

    for _ in range(weeks_ahead):
        if next_date >= today:
            existing = Course.query.filter_by(
                course_group_id=group.id,
                date=next_date,
            ).first()
            if not existing:
                course = Course(
                    course_group_id=group.id,
                    teacher_id=group.teacher_id,
                    date=next_date,
                    status="upcoming",
                )
                new_courses.append(course)
        next_date += timedelta(days=7)

    return new_courses
