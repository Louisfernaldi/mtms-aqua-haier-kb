var KB_FILES = [
  "brand.json",
  "induksi-kulkas.json",
  "induksi-water.json",
  "induksi-tv.json",
  "induksi-coldchain.json",
  "produk-kulkas.json",
  "produk-lain.json",
  "rotasi-pasar.json",
  "rotasi-benchmark.json",
  "rotasi-dealer.json",
  "proses.json",
  "tugas.json"
];
var KB_INDEX = [];
var KB_LOADED = false;

async function loadKbIndex() {
  if (KB_LOADED) return;
  for (var i = 0; i < KB_FILES.length; i++) {
    try {
      var j;
      if (window.MTMS_DATA && window.MTMS_DATA.knowledge && window.MTMS_DATA.knowledge[KB_FILES[i]]) {
        j = window.MTMS_DATA.knowledge[KB_FILES[i]];
      } else {
        j = await fetch("data/knowledge/" + KB_FILES[i]).then(function (r) {
          return r.json();
        });
      }
      for (var k = 0; k < j.fakta.length; k++) {
        KB_INDEX.push({
          kategori: j.kategori,
          judul: j.fakta[k].judul,
          isi: j.fakta[k].isi,
          sumber: j.fakta[k].sumber
        });
      }
    } catch (e) { /* file tidak ada: lanjut */ }
  }
  KB_LOADED = true;
}

function openSearch() {
  loadKbIndex().then(function () {
    document.getElementById("search-overlay").classList.add("open");
    document.getElementById("search-input").value = "";
    document.getElementById("search-results").innerHTML =
      '<div class="search-empty">Ketik kata kunci (mis. garansi, kompresor, SBS, GFK)...</div>';
    setTimeout(function () {
      document.getElementById("search-input").focus();
    }, 50);
  });
}
function closeSearch() {
  document.getElementById("search-overlay").classList.remove("open");
}
function doSearch() {
  var q = document.getElementById("search-input").value.trim().toLowerCase();
  var box = document.getElementById("search-results");
  if (q.length < 2) {
    box.innerHTML = '<div class="search-empty">Ketik minimal 2 huruf.</div>';
    return;
  }
  var out = [];
  for (var i = 0; i < KB_INDEX.length; i++) {
    var it = KB_INDEX[i];
    var hay = (it.kategori + " " + it.judul + " " + it.isi + " " + it.sumber).toLowerCase();
    if (hay.indexOf(q) !== -1) out.push(it);
    if (out.length >= 30) break;
  }
  if (!out.length) {
    box.innerHTML = '<div class="search-empty">Tidak ditemukan untuk "' + q + '". Coba kata lain.</div>';
    return;
  }
  box.innerHTML = out
    .map(function (r) {
      return (
        '<div class="r"><b>' + esc(r.judul) + "</b><br>" + esc(r.isi) +
        '<div class="s">' + esc(r.kategori) + " · " + esc(r.sumber) + "</div></div>"
      );
    })
    .join("");
}
function esc(s) {
  var d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    closeSearch();
    closeLightbox && closeLightbox();
  }
  if (e.key === "Enter" && document.getElementById("search-overlay").classList.contains("open")) doSearch();
});
