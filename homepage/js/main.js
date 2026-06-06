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

});
