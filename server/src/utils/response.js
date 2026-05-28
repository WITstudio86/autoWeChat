function sendJson(res, data, status = 200) {
  res.status(status).json(data);
}

function sendError(res, message, status = 400) {
  res.status(status).json({ error: message });
}

module.exports = { sendJson, sendError };
