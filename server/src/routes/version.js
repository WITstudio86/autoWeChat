const express = require('express');
const router = express.Router();

const GITHUB_API = 'https://api.github.com/repos/WITstudio86/autoWeChat/releases/latest';
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

let cache = null;
let cacheTime = 0;

router.get('/latest', async (req, res) => {
  try {
    const now = Date.now();
    if (cache && (now - cacheTime) < CACHE_TTL) {
      return res.json(cache);
    }

    const resp = await fetch(GITHUB_API, {
      headers: {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'autoWeChat-server',
      },
    });

    if (!resp.ok) {
      // Return cached data if available, otherwise error
      if (cache) return res.json(cache);
      return res.status(502).json({ error: '无法获取版本信息' });
    }

    const release = await resp.json();
    const version = (release.tag_name || '').replace(/^v/, '');
    const assets = (release.assets || [])
      .filter(a => a.name && a.name.endsWith('.zip'))
      .map(a => ({
        name: a.name,
        browser_download_url: a.browser_download_url,
        size: a.size,
      }));

    cache = {
      version,
      assets,
      published_at: release.published_at,
      html_url: release.html_url || 'https://wechat.zelab.top',
    };
    cacheTime = now;

    res.json(cache);
  } catch (err) {
    console.error('[version]', err.message);
    if (cache) return res.json(cache);
    res.status(502).json({ error: '无法获取版本信息' });
  }
});

module.exports = router;
