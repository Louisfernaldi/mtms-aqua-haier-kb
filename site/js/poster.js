/* Tiket 09 - pajangan poster B2B. Daftar file dirender dari manifest compose (nol hardcode nama file). */
(function () {
  "use strict";

  var MANIFEST_URL = "assets/poster/manifest.json";

  var LABEL_LINI = {
    kulkas: "Refrigerator",
    coldchain: "Cold Chain",
    water: "Water Solution",
    tvac: "TV & AC"
  };
  var LABEL_FMT = { feed: "Feed 1080x1350", story: "Story 1080x1920", a4: "Cetak A4" };

  var semua = [];

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function isiFilter(id, nilaiList, labelFn) {
    var sel = document.getElementById(id);
    nilaiList.forEach(function (v) {
      var opt = document.createElement("option");
      opt.value = v;
      opt.textContent = labelFn(v);
      sel.appendChild(opt);
    });
  }

  function render() {
    var lini = document.getElementById("liniFilter").value;
    var fmt = document.getElementById("fmtFilter").value;
    var grid = document.getElementById("gridPoster");
    grid.textContent = "";
    var tampil = semua.filter(function (p) {
      return (!lini || p.lini === lini) && (!fmt || p.format === fmt);
    });
    tampil.forEach(function (p) {
      var kartu = el("article", "kartu-poster");
      var gambar = el("img", "thumb-poster");
      gambar.src = p.file;
      gambar.alt = "Poster " + LABEL_LINI[p.lini] + " format " + p.format;
      gambar.loading = "lazy";
      kartu.appendChild(gambar);
      var badan = el("div", "badan-poster");
      badan.appendChild(el("h3", null, LABEL_LINI[p.lini]));
      badan.appendChild(el("span", "chip chip-fmt", LABEL_FMT[p.format] || p.format));
      var unduh = el("a", "tombol-unduh", "Unduh PNG");
      unduh.href = p.file;
      unduh.download = "";
      badan.appendChild(unduh);
      kartu.appendChild(badan);
      grid.appendChild(kartu);
    });
    document.getElementById("posterSummary").textContent =
      tampil.length + " dari " + semua.length + " poster ditampilkan.";
  }

  fetch(MANIFEST_URL)
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (m) {
      semua = m.posters || [];
      if (!semua.length) throw new Error("manifest kosong");
      var linis = [];
      var fmts = [];
      semua.forEach(function (p) {
        if (linis.indexOf(p.lini) === -1) linis.push(p.lini);
        if (fmts.indexOf(p.format) === -1) fmts.push(p.format);
      });
      isiFilter("liniFilter", linis.sort(), function (v) { return LABEL_LINI[v] || v; });
      isiFilter("fmtFilter", fmts.sort(), function (v) { return LABEL_FMT[v] || v; });
      document.getElementById("liniFilter").addEventListener("change", render);
      document.getElementById("fmtFilter").addEventListener("change", render);
      render();
    })
    .catch(function (e) {
      document.getElementById("posterSummary").textContent =
        "Gagal memuat daftar poster: " + e.message;
    });
})();
