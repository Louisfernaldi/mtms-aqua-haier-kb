/* kompetitor.js — Section "AQUA vs Kompetitor" (tiket D). ES5, pola produk.js. */
(function () {
  "use strict";

  var _data = null;
  var _activeCat = null;

  function fmtRp(n) {
    if (n === null || n === undefined) return "-";
    var jt = n / 1000000;
    var s = (Math.round(jt * 10) / 10).toString().replace(".", ",");
    return "Rp " + s + " jt";
  }

  function fmtRange(min, max) {
    if (min === null || max === null || min === undefined || max === undefined) return "-";
    if (min === max) return String(min) + " L";
    return min + "–" + max + " L";
  }

  function srcLabel(v) {
    if (!v) return "tanpa sumber";
    var s = String(v).toLowerCase();
    if (s.indexOf("gfk") !== -1) return "GFK";
    if (s.indexOf("official") !== -1 || s.indexOf("lg.com") !== -1) return "official-page";
    return String(v);
  }

  function srcSummary(models) {
    var counts = {};
    var noSrc = 0;
    models.forEach(function (m) {
      var lab = srcLabel(m.price_source);
      if (lab === "tanpa sumber") { noSrc++; return; }
      counts[lab] = (counts[lab] || 0) + 1;
    });
    var parts = Object.keys(counts).sort().map(function (k) { return k + " (" + counts[k] + ")"; });
    if (noSrc > 0) parts.push(noSrc + " tanpa sumber");
    return parts.length ? parts.join(" · ") : "-";
  }

  function modelsOf(brandRec, cat) {
    return (brandRec.models || []).filter(function (m) { return m.cat === cat; });
  }

  function statCat(models) {
    var caps = [], prices = [];
    models.forEach(function (m) {
      if (m.capacity_l !== null && m.capacity_l !== undefined) caps.push(m.capacity_l);
      if (m.price_idr !== null && m.price_idr !== undefined) prices.push(m.price_idr);
    });
    return {
      count: models.length,
      capMin: caps.length ? Math.min.apply(null, caps) : null,
      capMax: caps.length ? Math.max.apply(null, caps) : null,
      priceMin: prices.length ? Math.min.apply(null, prices) : null,
      priceMax: prices.length ? Math.max.apply(null, prices) : null
    };
  }

  function fiturAQUA(aquaRec, cat) {
    var out = [];
    aquaRec.models.forEach(function (m) {
      if (out.length >= 3) return;
      if (m.cat !== cat || !m.fitur || !m.fitur.length) return;
      out.push("<li><b>" + m.model + "</b>: " + m.fitur.join(" · ") + "</li>");
    });
    return out.length ? out.join("") : "<li>-</li>";
  }

  function esc(s) {
    return String(s === null || s === undefined ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function tableHtml(catCode) {
    var cats = (_data.categories || []).filter(function (c) { return c.code === catCode; });
    var label = cats.length ? cats[0].label : catCode;
    var aquaRec = null, comps = [];
    _data.brands.forEach(function (b) {
      if (b.brand === "AQUA") aquaRec = b; else comps.push(b);
    });
    var aq = statCat(modelsOf(aquaRec, catCode));
    var compModels = [];
    comps.forEach(function (b) { compModels = compModels.concat(modelsOf(b, catCode)); });
    var cp = statCat(compModels);

    var rows = [
      ["Jumlah model", String(aq.count), String(cp.count)],
      ["Kapasitas (L)", fmtRange(aq.capMin, aq.capMax), fmtRange(cp.capMin, cp.capMax)],
      ["Harga", (aq.priceMin !== null ? fmtRp(aq.priceMin) + " – " + fmtRp(aq.priceMax) : "-"),
        (cp.priceMin !== null ? fmtRp(cp.priceMin) + " – " + fmtRp(cp.priceMax) : "-")],
      ["Contoh fitur andalan (AQUA)", '<ul class="komp-feat">' + fiturAQUA(aquaRec, catCode) + "</ul>", "-"],
      ["Sumber harga", srcSummary(modelsOf(aquaRec, catCode)), srcSummary(compModels)]
    ];
    var trs = rows.map(function (r) {
      return "<tr><td>" + r[0] + "</td><td>" + r[1] + "</td><td>" + r[2] + "</td></tr>";
    }).join("");

    var compNames = comps.map(function (b) { return b.brand; }).join(", ");
    return '<div class="ringkasan-blok komp-tbl-blok">' +
      '<h3 class="ringkasan-judul">' + esc(label) + " — AQUA vs Rata-rata Kompetitor</h3>" +
      '<div class="tbl-scroll"><table class="komp-tbl">' +
      "<thead><tr><th>Aspek</th><th>AQUA</th><th>Kompetitor (" + esc(compNames) + ")</th></tr></thead>" +
      "<tbody>" + trs + "</tbody></table></div>" +
      '<p class="sec-sub rk-sumber">Rata-rata kompetitor = gabungan ' + esc(compNames) +
      ". Semua angka dihitung mesin dari data riset brand (found: true); sumber per harga lihat baris Sumber harga (official-page = situs resmi, GFK = riset harga GFK).</p>" +
      "</div>";
  }

  function chipsHtml() {
    var chips = (_data.categories || []).map(function (c) {
      return '<button type="button" class="pk-chip' + (c.code === _activeCat ? " on" : "") +
        '" data-cat="' + c.code + '">' + esc(c.label) + "</button>";
    }).join("");
    return '<div class="pk-chips komp-chips" id="komp-chips">' + chips + "</div>";
  }

  function escJs(s) {
    return esc(s).replace(/'/g, "&#39;");
  }

  function pdfCardHtml() {
    var p = _data.pdf || {};
    var size = p.size_mb ? p.size_mb : (p.size_bytes ? (p.size_bytes / 1048576).toFixed(1) + " MB" : "-");
    var path = p.path || "files/KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf";
    var file = p.file || "KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf";
    return '<div class="ringkasan-blok komp-dl-card">' +
      '<div><h3 class="ringkasan-judul">📄 Komparasi Kulkas AQUA vs 5 Brand — PDF Final</h3>' +
      '<p class="sec-sub" style="margin-bottom:0">' + esc(file) +
      " · " + esc(size) + "</p></div>" +
      '<div class="komp-dl-actions">' +
      '<a class="btn" href="' + esc(path) +
      '" download="' + esc(file) + '">Unduh PDF</a>' +
      '<button type="button" class="btn btn-sec" onclick="bukaPdfPreview(\'' + escJs(path) + '\')">Preview PDF</button>' +
      "</div>" +
      "</div>";
  }

  function renderAll() {
    var host = document.getElementById("konten-kompetitor");
    if (!host) return;
    host.innerHTML = pdfCardHtml() + chipsHtml() +
      '<div id="komp-tbl">' + tableHtml(_activeCat) + "</div>";
    var btns = host.querySelectorAll("#komp-chips .pk-chip");
    for (var i = 0; i < btns.length; i++) {
      btns[i].onclick = (function (code) {
        return function () {
          _activeCat = code;
          var cur = host.querySelectorAll("#komp-chips .pk-chip");
          for (var j = 0; j < cur.length; j++) {
            cur[j].className = "pk-chip" + (cur[j].getAttribute("data-cat") === code ? " on" : "");
          }
          var tbl = document.getElementById("komp-tbl");
          if (tbl) tbl.innerHTML = tableHtml(code);
        };
      })(btns[i].getAttribute("data-cat"));
    }
  }

  function gotData(d) {
    _data = d;
    var cats = (d.categories || []).map(function (c) { return c.code; });
    _activeCat = cats.length ? cats[0] : null;
    renderAll();
  }

  window.renderKompetitor = function () {
    var D = window.MTMS_DATA || {};
    if (D.kompetitor) {
      gotData(D.kompetitor);
      return;
    }
    fetch("data/kompetitor.json")
      .then(function (r) { return r.json(); })
      .then(gotData)
      .catch(function () {
        var host = document.getElementById("konten-kompetitor");
        if (host) host.innerHTML = '<p class="sec-sub">Data kompetitor gagal dimuat.</p>';
      });
  };
})();