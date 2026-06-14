/**
 * autoWeChat Homepage — Main JS
 */

document.addEventListener('DOMContentLoaded', function () {

  // ---- Smooth scrolling for anchor links ----
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ---- OS detection: highlight recommended download card ----
  (function () {
    var plat = navigator.platform || '';
    var isMac = /Mac|iPhone|iPad|iPod/i.test(plat) || /Mac/i.test(navigator.userAgent);
    var isWin = /Win/i.test(plat);

    var macCard = document.getElementById('downloadMac');
    var winCard = document.getElementById('downloadWindows');
    var macBadge = document.getElementById('macRecommend');
    var winBadge = document.getElementById('winRecommend');

    if (isMac && macCard) {
      macCard.classList.add('recommended');
      if (macBadge) macBadge.classList.remove('d-none');
    } else if (isWin && winCard) {
      winCard.classList.add('recommended');
      if (winBadge) winBadge.classList.remove('d-none');
    }
  })();

  // ---- Navbar shadow on scroll ----
  (function () {
    var navbar = document.querySelector('.navbar');
    if (!navbar) return;

    window.addEventListener('scroll', function () {
      if (window.scrollY > 10) {
        navbar.classList.add('shadow-sm');
      } else {
        navbar.classList.remove('shadow-sm');
      }
    });
  })();

  // ---- Fetch latest version ----
  (function () {
    var macVer = document.getElementById('dlMacVersion');
    var winVer = document.getElementById('dlWinVersion');
    var macLink = document.getElementById('dlMacLink');
    var winLink = document.getElementById('dlWinLink');

    var GITHUB_API = 'https://api.github.com/repos/WITstudio86/autoWeChat/releases/latest';

    function applyData(data) {
      if (!data || !data.version) return;
      var v = 'v' + data.version;
      if (macVer) macVer.textContent = v;
      if (winVer) winVer.textContent = v;

      var assets = data.assets || [];
      function pickAsset(keyword) {
        var exact = assets.find(function (a) { return a.name === 'autoWeChat-' + keyword + '.zip'; });
        if (exact) return exact;
        return assets.find(function (a) { return a.name && a.name.indexOf(keyword) !== -1; });
      }

      var macAsset = pickAsset('macOS');
      var winAsset = pickAsset('windows');

      if (macAsset && macLink) macLink.href = macAsset.browser_download_url;
      if (winAsset && winLink) winLink.href = winAsset.browser_download_url;
    }

    function parseGitHubRelease(data) {
      var version = (data.tag_name || '').replace(/^v/, '');
      var assets = (data.assets || []).map(function (a) {
        return { name: a.name, browser_download_url: a.browser_download_url, size: a.size };
      });
      return { version: version, assets: assets };
    }

    // Try server API first (fast, cached), fallback to GitHub API directly
    fetch('/api/version/latest')
      .then(function (r) { return r.json(); })
      .then(applyData)
      .catch(function () {
        return fetch(GITHUB_API, { headers: { 'Accept': 'application/vnd.github+json' } })
          .then(function (r) { return r.json(); })
          .then(function (data) { applyData(parseGitHubRelease(data)); })
          .catch(function () { /* keep defaults */ });
      });
  })();

});
