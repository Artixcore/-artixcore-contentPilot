(function () {
  'use strict';

  function getShell() {
    return document.querySelector('.cp-shell');
  }

  function initMobileMenu() {
    document.addEventListener('click', function (e) {
      var toggle = e.target.closest('#cp-menu-toggle');
      var shell = getShell();
      if (!shell) return;

      if (toggle) {
        e.preventDefault();
        shell.classList.toggle('cp-sidebar-open');
        return;
      }

      if (window.innerWidth > 1199) return;

      var sidebar = document.getElementById('cp-sidebar');
      if (!sidebar || !shell.classList.contains('cp-sidebar-open')) return;

      if (!sidebar.contains(e.target) && !toggle) {
        shell.classList.remove('cp-sidebar-open');
      }
    });
  }

  function onResize() {
    var shell = getShell();
    if (shell && window.innerWidth > 1199) {
      shell.classList.remove('cp-sidebar-open');
    }
  }

  function onReady() {
    initMobileMenu();
    window.addEventListener('resize', onResize);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }
})();
