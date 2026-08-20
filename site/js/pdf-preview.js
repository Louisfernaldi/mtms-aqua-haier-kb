/* pdf-preview.js — Modal preview PDF via iframe (fitur H2). ES5, pola produk.js. */
(function () {
  "use strict";

  var STYLE_ID = "pdf-preview-css";
  var css = [
    ".pdf-preview-overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:120;display:flex;align-items:center;justify-content:center;padding:16px;}",
    ".pdf-preview-box{position:relative;background:#fff;width:90vw;max-width:1200px;height:85vh;border-radius:10px;box-shadow:0 14px 50px rgba(0,0,0,.4);overflow:hidden;}",
    ".pdf-preview-close{position:absolute;top:4px;right:10px;background:none;border:none;font-size:1.7rem;line-height:1;color:#555;cursor:pointer;z-index:2;width:38px;height:38px;}",
    ".pdf-preview-close:hover{color:#000;}",
    ".pdf-preview-iframe{display:block;width:100%;height:calc(100% - 40px);border:none;}",
    ".btn-preview{background:var(--bg-soft);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:4px 12px;font-size:0.8rem;font-weight:600;cursor:pointer;}",
    ".btn-preview:hover{background:var(--accent-soft);border-color:var(--accent);}"
  ].join("\n");

  function ensureCss() {
    if (document.getElementById(STYLE_ID)) return;
    var st = document.createElement("style");
    st.id = STYLE_ID;
    st.textContent = css;
    document.head.appendChild(st);
  }

  function onKey(e) {
    if (e.key === "Escape") window.buatClosePdfPreview();
  }

  window.bukaPdfPreview = function (path) {
    ensureCss();
    window.buatClosePdfPreview();
    var overlay = document.createElement("div");
    overlay.className = "pdf-preview-overlay";
    overlay.innerHTML =
      '<div class="pdf-preview-box">' +
      '<button type="button" class="pdf-preview-close" aria-label="Tutup preview">&times;</button>' +
      '<iframe class="pdf-preview-iframe" src="' + path + '" title="Preview PDF"></iframe>' +
      "</div>";
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) window.buatClosePdfPreview();
    });
    overlay.querySelector(".pdf-preview-close").onclick = window.buatClosePdfPreview;
    document.addEventListener("keydown", onKey);
    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";
  };

  window.buatClosePdfPreview = function () {
    var ov = document.querySelector(".pdf-preview-overlay");
    if (ov && ov.parentNode) ov.parentNode.removeChild(ov);
    document.removeEventListener("keydown", onKey);
    document.body.style.overflow = "";
  };
})();
