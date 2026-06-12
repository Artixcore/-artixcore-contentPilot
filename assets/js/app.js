(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
    } else {
      document.addEventListener("DOMContentLoaded", fn);
    }
  }

  ready(function () {
    document.addEventListener("click", function (event) {
      var toggle = event.target.closest("[data-cp-mobile-menu]");
      var sidebar = document.querySelector(".cp-sidebar");

      if (!toggle || !sidebar) return;

      event.preventDefault();
      sidebar.classList.toggle("cp-sidebar-open");
    });
  });
})();
