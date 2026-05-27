document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss flash messages after 3 seconds
    const alerts = document.querySelectorAll(".alert-auto-dismiss");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 3000);
    });
});

function confirmDelete(msg) {
    return confirm(msg || "确认删除？此操作不可撤销。");
}
