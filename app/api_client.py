import requests
from flask import session, current_app

SESSION_EXPIRED_MSG = "未登录或会话已过期，请刷新页面重新登录"


class ApiClient:
    """HTTP client for the remote Node.js API."""

    def __init__(self, base_url=None):
        self._base_url = base_url

    def set_base_url(self, url):
        """Update the server base URL at runtime."""
        self._base_url = url

    @property
    def base_url(self):
        if self._base_url:
            return self._base_url
        return current_app.config.get("SERVER_BASE_URL", "http://localhost:5001")

    def _headers(self, extra=None):
        jwt = session.get("jwt", "")
        h = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
        if extra:
            h.update(extra)
        return h

    def _get(self, path, params=None, timeout=15):
        r = requests.get(f"{self.base_url}{path}", headers=self._headers(),
                        params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path, data=None, timeout=15):
        r = requests.post(f"{self.base_url}{path}", headers=self._headers(),
                         json=data, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def _put(self, path, data=None, timeout=15):
        r = requests.put(f"{self.base_url}{path}", headers=self._headers(),
                        json=data, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def _delete(self, path, timeout=15):
        r = requests.delete(f"{self.base_url}{path}", headers=self._headers(),
                           timeout=timeout)
        r.raise_for_status()
        return r.json()

    # ── Auth ──

    def login(self, username, password):
        return self._post("/api/auth/login", {"username": username, "password": password})

    def logout(self):
        try:
            self._post("/api/auth/logout")
        except Exception:
            pass

    def get_me(self):
        return self._get("/api/auth/me")

    # ── Groups ──

    def list_groups(self):
        return self._get("/api/groups")

    def create_group(self, data):
        return self._post("/api/groups", data)

    def get_group(self, gid):
        return self._get(f"/api/groups/{gid}")

    def update_group(self, gid, data):
        return self._put(f"/api/groups/{gid}", data)

    def delete_group(self, gid):
        return self._delete(f"/api/groups/{gid}")

    # ── Students ──

    def list_students(self, group_id=None, sort="name", filter_text=""):
        params = {}
        if group_id is not None:
            params["group_id"] = group_id
        if sort != "name":
            params["sort"] = sort
        if filter_text:
            params["filter"] = filter_text
        return self._get("/api/students", params)

    def create_student(self, data):
        return self._post("/api/students", data)

    def get_student(self, sid):
        return self._get(f"/api/students/{sid}")

    def update_student(self, sid, data):
        return self._put(f"/api/students/{sid}", data)

    def delete_student(self, sid):
        return self._delete(f"/api/students/{sid}")

    def move_student(self, sid, course_group_id):
        return self._post(f"/api/students/{sid}/move", {"course_group_id": course_group_id})

    # ── Templates ──

    def list_templates(self):
        return self._get("/api/templates")

    def create_template(self, data):
        return self._post("/api/templates", data)

    def get_template(self, tid):
        return self._get(f"/api/templates/{tid}")

    def update_template(self, tid, data):
        return self._put(f"/api/templates/{tid}", data)

    def delete_template(self, tid):
        return self._delete(f"/api/templates/{tid}")

    # ── Send Logs ──

    def create_send_log(self, data):
        return self._post("/api/send-logs", data)

    def list_send_logs(self, limit=100):
        return self._get("/api/send-logs", {"limit": limit})

    # ── Stats ──

    def get_stats(self):
        return self._get("/api/stats")

    # ── AI ──

    def generate_autocontent(self, description, timeout=60):
        return self._post("/api/ai/autocontent",
                          {"description": description}, timeout=timeout)

    def generate_performance(self, student_name, notes, course_context="", timeout=60):
        return self._post("/api/ai/performance",
                          {"student_name": student_name, "notes": notes,
                           "course_context": course_context}, timeout=timeout)

    # ── Settings ──

    def get_settings(self):
        return self._get("/api/settings")

    def update_settings(self, data):
        return self._put("/api/settings", data)

    # ── Admin ──

    def admin_list_teachers(self):
        return self._get("/api/admin/teachers")

    def admin_create_teacher(self, data):
        return self._post("/api/admin/teachers", data)

    def admin_update_teacher(self, tid, data):
        return self._put(f"/api/admin/teachers/{tid}", data)

    def admin_delete_teacher(self, tid):
        return self._delete(f"/api/admin/teachers/{tid}")

    def admin_reset_password(self, tid, password):
        return self._post(f"/api/admin/teachers/{tid}/reset-password", {"password": password})

    def admin_get_usage(self):
        return self._get("/api/admin/usage")

    def admin_toggle_active(self, tid):
        return self._post(f"/api/admin/teachers/{tid}/toggle-active")


# Singleton, initialized in create_app()
api = ApiClient()
