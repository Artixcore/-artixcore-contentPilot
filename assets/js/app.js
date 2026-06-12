(function () {
  'use strict';

  function syncBodyClasses() {
    var sidebar = document.querySelector('.cp-shell-sidebar');
    if (sidebar) {
      var hidden = sidebar.closest('[data-testid="column"]');
      if (hidden && hidden.offsetParent === null) {
        document.body.classList.add('cp-sidebar-collapsed');
      }
    }
  }

  function initMobileOverlayClose() {
    document.addEventListener('click', function (e) {
      if (window.innerWidth > 1024) return;
      var sidebar = document.querySelector('.cp-shell-sidebar');
      if (!sidebar) return;
      var sidebarBlock = sidebar.closest('[data-testid="stVerticalBlock"]');
      if (!sidebarBlock || sidebarBlock.offsetParent === null) return;
      if (sidebar.contains(e.target)) return;
      var menuBtn = document.querySelector('.cp-menu-btn');
      if (menuBtn && menuBtn.contains(e.target)) return;
      var toggle = document.querySelector('[data-testid="baseButton-secondary"]');
      if (toggle && toggle.closest('.cp-menu-btn') && toggle.contains(e.target)) return;
    });
  }

  function onReady() {
    syncBodyClasses();
    initMobileOverlayClose();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }

  var observer = new MutationObserver(function () {
    syncBodyClasses();
  });

  observer.observe(document.body, { childList: true, subtree: true });
})();
