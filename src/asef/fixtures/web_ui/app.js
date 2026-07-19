(() => {
  "use strict";

  const form = document.querySelector("#checklist");
  const checks = [...form.querySelectorAll('input[type="checkbox"]')];
  const note = document.querySelector("#review-note");
  const summary = document.querySelector("#summary");
  const result = document.querySelector("#result");
  const reset = document.querySelector("#reset");

  function renderSummary() {
    const completed = checks.filter((item) => item.checked).length;
    summary.textContent = `${completed} of ${checks.length} checks complete`;
  }

  function resetFixture() {
    form.reset();
    result.textContent = "No review saved";
    renderSummary();
  }

  checks.forEach((item) => item.addEventListener("change", renderSummary));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    result.textContent = note.value.trim() || "Review saved";
  });
  reset.addEventListener("click", resetFixture);
  resetFixture();
})();
