document.addEventListener("DOMContentLoaded", function () {
  // Show an "Analyzing..." state on submit. There is no polling here - the
  // browser is simply waiting on the one synchronous request while
  // Playwright loads and audits the page server-side.
  document.querySelectorAll("form[action*='analyze']").forEach(function (form) {
    form.addEventListener("submit", function () {
      var button = form.querySelector("button[type=submit]");
      if (button && !button.disabled) {
        button.disabled = true;
        button.textContent = "Analyzing…";
        button.classList.add("opacity-70", "cursor-not-allowed");
      }
    });
  });

  // Client-side filtering of the already-rendered issues table - no extra
  // requests, just show/hide rows by their data-status attribute.
  var filterButtons = document.querySelectorAll(".filter-btn");
  var rows = document.querySelectorAll(".issue-row");
  if (!filterButtons.length) return;

  filterButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      filterButtons.forEach(function (b) {
        b.classList.remove("bg-slate-900", "text-white");
        b.classList.add("text-slate-600");
      });
      btn.classList.add("bg-slate-900", "text-white");
      btn.classList.remove("text-slate-600");

      var filter = btn.dataset.filter;
      rows.forEach(function (row) {
        row.style.display = (filter === "all" || row.dataset.status === filter) ? "" : "none";
      });
    });
  });
});
