(function () {
  var saved = localStorage.getItem("ty-theme");
  if (saved === "dark") document.documentElement.setAttribute("data-theme", "dark");
})();
function toggleTheme() {
  var cur = document.documentElement.getAttribute("data-theme");
  var next = cur === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("ty-theme", next);
}
