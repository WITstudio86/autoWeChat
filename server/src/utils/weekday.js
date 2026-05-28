const WEEKDAY_OPTIONS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const WEEKDAY_MAP = new Map(WEEKDAY_OPTIONS.map((v, i) => [v, i]));

module.exports = { WEEKDAY_OPTIONS, WEEKDAY_MAP };
