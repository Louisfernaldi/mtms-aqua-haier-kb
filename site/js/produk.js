function renderRingkasan(targetId) {
  var host = document.getElementById(targetId);
  if (!host) return;
  var D = window.MTMS_DATA || {};
  var katalog = D.katalog || [];
  if (!katalog.length) {
    host.innerHTML = '<p class="sec-sub">Ringkasan gagal dimuat.</p>';
    return;
  }
  var kb = D.knowledge && D.knowledge["produk-kulkas.json"];
  var ringkasan = D.ringkasan || hitungRingkasan(katalog, kb);

  function numLead(s) {
    if (s === null || s === undefined) return null;
    var m = String(s).match(/\s*(\d+(?:[.,]\d+)?)/);
    return m ? parseFloat(m[1].replace(",", ".")) : null;
  }

  function hitungRingkasan(kat, kb2) {
    var order = ["Single Door", "Top Mount", "Bottom Mount", "Side by Side", "Multidoor"];
    var hargaMap = {};
    ((kb2 && kb2.segmen_harga) || []).forEach(function (sh) { hargaMap[sh.segmen] = sh; });
    var segmen = order.map(function (g) {
      var rows = kat.filter(function (p) { return p.group === g; });
      var caps = rows.map(function (p) { return p.kapasitas_gross; }).filter(function (c) { return c != null; });
      var sh = hargaMap[g] || {};
      return {
        segmen: g,
        label: sh.label || g,
        rentang: sh.rentang || "-",
        sumber: sh.sumber || "-",
        jumlah_model: rows.length,
        kapasitas_min: caps.length ? Math.min.apply(null, caps) : null,
        kapasitas_max: caps.length ? Math.max.apply(null, caps) : null
      };
    });
    var gar = [], daya = [];
    kat.forEach(function (p) {
      var g = numLead(p.garansi_tahun), d = numLead(p.daya_watt);
      if (g != null) gar.push({ n: g, label: p.garansi_tahun, model: p.model });
      if (d != null) daya.push({ n: d, label: p.daya_watt, model: p.model });
    });
    gar.sort(function (a, b) { return b.n - a.n; });
    daya.sort(function (a, b) { return a.n - b.n; });
    var minD = daya.length ? daya[0].n : null;
    var stats = {
      garansi_terpanjang: gar.length ? { nilai: Math.round(gar[0].n), label: gar[0].label, model: gar[0].model } : null,
      daya_terhemat: {
        nilai: minD,
        label: daya.length ? daya[0].label : null,
        models: daya.filter(function (x) { return x.n === minD; }).map(function (x) { return x.model; }).sort()
      },
      jumlah_model: kat.length,
      jumlah_varian: kat.reduce(function (acc, p) { return acc + (p.varian ? p.varian.length : 0); }, 0)
    };
    return { segmen: segmen, stats: stats, sumber: "dihitung di browser dari JSON (fallback, data.js belum ber-ringkasan)" };
  }

  function fmtRentang(r) {
    if (!r || r === "-") return "-";
    return "Rp " + r.replace(/-/g, "–").replace(/\s*juta/g, " juta");
  }

  function fmtAngka(n) {
    if (n === null || n === undefined) return "-";
    return (n % 1 === 0) ? String(n) : String(n).replace(".", ",");
  }

  var html = "";

  var rows = ringkasan.segmen.map(function (s) {
    return "<tr><td>" + s.label + "</td><td>" + fmtRentang(s.rentang) +
      (s.sumber && s.sumber !== "-" ? ' <span class="src">(' + s.sumber + ")</span>" : "") +
      "</td><td>" + s.jumlah_model + "</td><td>" +
      (s.kapasitas_min != null ? s.kapasitas_min + "–" + s.kapasitas_max + " L gross" : "-") +
      "</td></tr>";
  }).join("");
  html += '<div class="ringkasan-blok">' +
    '<h3 class="ringkasan-judul">Segmen &amp; Harga</h3>' +
    "<table><thead><tr><th>Segmen</th><th>Rentang Harga (Rp)</th><th>Jumlah Model</th><th>Kapasitas Range</th></tr></thead>" +
    "<tbody>" + rows + "</tbody></table>" +
    '<p class="sec-sub rk-sumber">Rentang harga per segmen dari Aqua PM; jumlah model &amp; kapasitas dihitung mesin dari katalog. ' +
    (ringkasan.sumber || "") + ".</p>" +
    "</div>";

  var st = ringkasan.stats || {};
  html += '<div class="ringkasan-blok"><h3 class="ringkasan-judul">Angka Penting</h3><div class="ringkasan-stats">';
  function statCard(nilai, sub) {
    return '<div class="stat-card"><b>' + nilai + "</b><span>" + sub + "</span></div>";
  }
  if (st.garansi_terpanjang && st.garansi_terpanjang.nilai != null) {
    html += statCard(st.garansi_terpanjang.nilai + " th", "Garansi kompresor terpanjang · " + (st.garansi_terpanjang.label || ""));
  }
  if (st.daya_terhemat && st.daya_terhemat.nilai != null) {
    var dm = (st.daya_terhemat.models || []).slice(0, 2).join(", ");
    var dmore = (st.daya_terhemat.models || []).length > 2 ? " dkk" : "";
    html += statCard(fmtAngka(st.daya_terhemat.nilai) + " W", "Daya terhemat · " + dm + dmore);
  }
  if (st.jumlah_model != null) html += statCard(st.jumlah_model, "Jumlah model katalog");
  if (st.jumlah_varian != null) html += statCard(st.jumlah_varian, "Jumlah varian / pilihan warna");
  html += "</div></div>";

  var bulletJudul = ["Seri AQR-D (1 pintu)", "Keunggulan seri AQR-D", "Analisa segmen (Aqua PM)", "Model unggulan MD (Haier)"];
  if (kb && kb.fakta) {
    var bullets = [];
    bulletJudul.forEach(function (j) {
      var f = null;
      kb.fakta.forEach(function (x) { if (x.judul === j) f = x; });
      if (!f) return;
      var poin = f.isi.split(/(?:\. )|(?: — )/).map(function (t) { return t.trim(); }).filter(Boolean).slice(0, 3);
      var lis = poin.map(function (t) { return "<li>" + t + "</li>"; }).join("");
      var ico = (typeof faktaEmoji === "function") ? faktaEmoji(f.judul, f.isi) : "📄";
      bullets.push(
        '<div class="card ringkasan-bullet"><h3><span class="fakta-ico">' + ico + "</span>" + f.judul + "</h3>" +
        '<ul class="rk-bullets">' + lis + "</ul>" +
        '<span class="src">Sumber: ' + f.sumber + "</span></div>"
      );
    });
    if (bullets.length) {
      html += '<div class="ringkasan-blok"><h3 class="ringkasan-judul">Fakta Singkat</h3>' +
        '<div class="ringkasan-bullets">' + bullets.join("") + "</div></div>";
    }
  }

  host.innerHTML = html;
}

function renderKatalog(targetId) {
  var host = document.getElementById(targetId);
  if (!host) return;
  function loadKatalog() {
    function fallback() {
      if (window.MTMS_DATA && window.MTMS_DATA.katalog && window.MTMS_DATA.katalog.length) {
        return Promise.resolve(window.MTMS_DATA.katalog);
      }
      return fetch("data/produk-katalog.json").then(function (r) { return r.json(); });
    }
    if (window.location.protocol !== "http:" && window.location.protocol !== "https:") {
      return Promise.resolve((window.MTMS_DATA && window.MTMS_DATA.katalog) || []);
    }
    // coba data live dari API (editable). Kalau gagal, pakai data bawaan.
    return fetch("api/produk").then(function (r) {
      if (!r.ok) throw new Error("api " + r.status);
      return r.json();
    }).then(function (items) {
      return loadManifest().then(function (files) {
        items.forEach(function (p) {
          // foto_list eksplisit (hasil edit/upload) dipakai apa adanya; kalau kosong, hitung otomatis dari file
          if (!p.foto_list || !p.foto_list.length) {
            p.foto_list = computeFotoList(p.model, p.foto, files);
          }
        });
        // merge fitur dari data bawaan (data.js) biar "Fitur Unggulan" tetap tampil
        var embedded = (window.MTMS_DATA && window.MTMS_DATA.katalog) || [];
        var fiturMap = {};
        embedded.forEach(function (e) { if (e.model && e.fitur && e.fitur.length) fiturMap[e.model] = e.fitur; });
        items.forEach(function (p) { if (!p.fitur && fiturMap[p.model]) p.fitur = fiturMap[p.model]; });
        window.MTMS_MANIFEST = files;
        window.MTMS_DATA_LIVE = true;
        return items;
      });
    }).catch(fallback);
  }
  loadKatalog()
    .then(function (items) {
      var state = { group: "Semua", q: "", page: 1, pageSize: 12 };

      var chips = document.createElement("div");
      chips.className = "pk-chips";
      var groups = ["Semua", "Single Door", "Top Mount", "Bottom Mount", "Side by Side", "Multidoor"];
      groups.forEach(function (g, i) {
        var c = document.createElement("button");
        c.className = "pk-chip" + (g === state.group ? " on" : "");
        c.textContent = g + " (" + (g === "Semua" ? items.length : items.filter(function (x) { return x.group === g; }).length) + ")";
        c.onclick = function () {
          state.group = g;
          state.page = 1;
          chips.querySelectorAll(".pk-chip").forEach(function (ch) { ch.classList.remove("on"); });
          c.classList.add("on");
          render();
        };
        chips.appendChild(c);
      });
      host.appendChild(chips);

      var info = document.createElement("p");
      info.className = "sec-sub pk-info";
      host.appendChild(info);

      var grid = document.createElement("div");
      grid.className = "grid pk-grid";
      host.appendChild(grid);

      var pagination = document.createElement("div");
      pagination.className = "pk-pagination";
      host.appendChild(pagination);

      function fmtFlag(f) {
        var map = { "Inverter": "Inverter", "Non-Inverter": "Non-Inverter", "Import Thailand": "Import Thailand", "Flagship": "Flagship", "Entry": "Entry", "Best Seller": "Best Seller", "Halo Product": "Halo Product" };
        return map[f] || f;
      }

      function fmtRp(n) {
        if (n === null || n === undefined || n === "") return "";
        var s = String(n).replace(/\./g, "").replace(/\D/g, "");
        if (!s) return "";
        return "Rp " + s.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      }

      function thumb(p) {
        var f0 = p.foto || (p.foto_list && p.foto_list.length ? p.foto_list[0] : null);
        if (f0) {
          return '<div class="pk-thumb"><img loading="lazy" src="' + f0 + '" alt="' + p.model + '"></div>';
        }
        var model = p.model || "";
        var label = "Belum ada foto";
        if (model) label += " · " + model;
        var svg = '<svg class="pk-noimg-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 7h10"/><path d="M7 11h6"/><path d="M7 15h4"/><line x1="12" y1="19" x2="12" y2="21"/></svg>';
        return '<div class="pk-thumb pk-noimg" aria-hidden="true">' + svg + '<span class="pk-noimg-label">' + label + '</span></div>';
      }

      function card(p) {
        var el = document.createElement("div");
        el.className = "pk-card";
        el.setAttribute("data-model", p.model);
        var flags = (p.flags || []).map(function (f) {
          return '<span class="badge ' + f.toLowerCase().replace(/[^a-z]+/g, "-") + '">' + fmtFlag(f) + "</span>";
        }).join("");
        el.innerHTML =
          '<div class="pk-card-top">' +
          '<span class="pk-cat">' + p.kategori + "</span>" +
          "<div>" + flags + "</div>" +
          "</div>" +
          thumb(p) +
          '<h3 class="pk-model">' + p.model + "</h3>" +
          '<p class="pk-cap">' +
          (p.kapasitas_gross ? p.kapasitas_gross + " L gross" : "") +
          (p.kapasitas_nett ? " / " + p.kapasitas_nett + " L nett" : "") +
          "</p>" +
          '<p class="pk-meta">' +
          (p.material ? "Pintu " + p.material : "") +
          (p.daya_watt ? " · " + p.daya_watt + " W" : "") +
          (p.garansi_tahun ? " · Garansi " + p.garansi_tahun + " th" : "") +
          "</p>" +
          (p.harga_idr ? '<p class="pk-price">' + fmtRp(p.harga_idr) + "</p>" : "");
        el.onclick = function () { openProductDetail(p); };
        return el;
      }

      function openProductDetail(p) {
        window.MTMSProductDetail.open(p, {
          onEdit: function (record) {
            if (window.__mtms_openEdit) window.__mtms_openEdit(record);
            else alert("Editor belum siap — refresh halaman");
          }
        });
      }

      function render() {
        var list = items.filter(function (p) {
          var okGroup = state.group === "Semua" || p.group === state.group;
          var q = state.q.trim().toLowerCase();
          var okQ = !q || p.model.toLowerCase().indexOf(q) !== -1 || (p.varian || []).join(" ").toLowerCase().indexOf(q) !== -1 || (p.benefit || "").toLowerCase().indexOf(q) !== -1;
          return okGroup && okQ;
        });

        var total = list.length;
        var start = (state.page - 1) * state.pageSize;
        var end = Math.min(start + state.pageSize, total);
        var pageItems = list.slice(start, end);

        info.textContent = "Menampilkan " + end + " dari " + total + " model kulkas AQUA (sumber: AQUA REF Product Mapping, Juli 2026). Klik kartu untuk detail.";
        grid.innerHTML = "";
        pageItems.forEach(function (p) { grid.appendChild(card(p)); });
        if (!pageItems.length) {
          grid.innerHTML = '<p class="sec-sub">Tidak ada produk cocok.</p>';
        }

        renderPagination(total);
        if (window.__mtms_after_render) window.__mtms_after_render();
      }

      function renderPagination(total) {
        var totalPages = Math.ceil(total / state.pageSize);
        if (totalPages <= 1) {
          pagination.innerHTML = "";
          return;
        }
        var html = "";
        if (state.page > 1) {
          html += '<button type="button" class="pk-page-btn" data-page="' + (state.page - 1) + '" aria-label="Halaman sebelumnya">‹ Prev</button>';
        }
        var maxButtons = 5;
        var startPage = Math.max(1, state.page - Math.floor(maxButtons / 2));
        var endPage = Math.min(totalPages, startPage + maxButtons - 1);
        if (endPage - startPage + 1 < maxButtons) {
          startPage = Math.max(1, endPage - maxButtons + 1);
        }
        for (var p = startPage; p <= endPage; p++) {
          html += '<button type="button" class="pk-page-btn' + (p === state.page ? " on" : "") + '" data-page="' + p + '">' + p + "</button>";
        }
        if (state.page < totalPages) {
          html += '<button type="button" class="pk-page-btn" data-page="' + (state.page + 1) + '" aria-label="Halaman berikutnya">Next ›</button>';
        }
        html += '<select class="pk-page-size" aria-label="Item per halaman">';
        [12, 24].forEach(function (sz) {
          html += '<option value="' + sz + '"' + (sz === state.pageSize ? " selected" : "") + ">" + sz + " per halaman</option>";
        });
        html += "</select>";
        pagination.innerHTML = html;
        pagination.querySelectorAll(".pk-page-btn").forEach(function (btn) {
          btn.onclick = function () {
            state.page = Number(this.getAttribute("data-page"));
            render();
            window.scrollTo({ top: chips.offsetTop - 80, behavior: "smooth" });
          };
        });
        pagination.querySelector(".pk-page-size").onchange = function () {
          state.pageSize = Number(this.value);
          state.page = 1;
          render();
        };
      }

      render();
      initEditor(items, host);
      var requestedModel = new URLSearchParams(window.location.search).get("model");
      if (requestedModel !== null) {
        var requestedProduct = items.find(function (item) { return item.model === requestedModel; });
        if (requestedProduct) openProductDetail(requestedProduct);
      }
    })
    .catch(function () {
      host.innerHTML = '<p class="sec-sub">Katalog gagal dimuat.</p>';
    });
}

// ================= EDITOR (edit dari website, simpan permanen via API) =================
// Data live (API) + daftar file foto. Kalau API nggak ada, editor nonaktif.

function loadManifest() {
  var local = fetch("data/produk-assets.json")
    .then(function (r) { return r.json(); })
    .then(function (d) { return (d.produk || []).map(function (n) { return { name: n, url: "assets/produk/" + n }; }); })
    .catch(function () { return []; });
  var remote = fetch("api/foto")
    .then(function (r) { return r.ok ? r.json() : { files: [] }; })
    .then(function (d) { return (d.files || []).map(function (n) { return { name: n, url: "https://raw.githubusercontent.com/Louisfernaldi/mtms-aqua-haier-kb-foto/main/" + encodeURIComponent(n) }; }); })
    .catch(function () { return []; });
  return Promise.all([local, remote]).then(function (parts) { return parts[0].concat(parts[1]); });
}

function computeFotoList(model, foto, files) {
  var prefix = (model || "").toLowerCase() + "__";
  var fotos = [];
  (files || []).forEach(function (f) {
    if (f.name.toLowerCase().indexOf(prefix) === 0) {
      fotos.push(f.url);
    }
  });
  function keyOf(u) {
    var m = u.match(/__(\d+)\./);
    if (m) return [0, parseInt(m[1], 10)];
    return [1, u.toLowerCase()];
  }
  fotos.sort(function (a, b) {
    var ka = keyOf(a), kb = keyOf(b);
    return ka[0] - kb[0] || (ka[1] < kb[1] ? -1 : ka[1] > kb[1] ? 1 : 0);
  });
  if (foto) {
    var i = fotos.indexOf(foto);
    if (i > 0) fotos.splice(i, 1);
    if (i !== 0) fotos.unshift(foto);
  }
  return fotos;
}

function initEditor(items, host) {
  if (!window.MTMS_DATA_LIVE) return;
  var files = window.MTMS_MANIFEST || [];

  // tombol "Tambah produk" (selalu muncul — situs sudah dikunci login)
  var addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "pk-edit-fab pk-edit-add";
  addBtn.textContent = "＋ Produk";
  addBtn.title = "Tambah produk baru";
  document.body.appendChild(addBtn);
  addBtn.onclick = function () { openEdit(null, files); };

  // tombol "Ganti password" (di atas tombol Tambah)
  var passBtn = document.createElement("button");
  passBtn.type = "button";
  passBtn.className = "pk-edit-fab pk-edit-pass";
  passBtn.textContent = "🔑";
  passBtn.title = "Ganti password login";
  document.body.appendChild(passBtn);
  passBtn.onclick = openPasswordModal;

  function openPasswordModal() {
    openOverlay(
      '<div class="pk-pw-box">' +
      '<h3 class="sec-title">Ganti password login</h3>' +
      '<p class="sec-sub">Password dipakai untuk masuk ke situs ini. Setelah diganti, semua sesi login lama otomatis keluar.</p>' +
      '<div class="pk-edit-field"><label>Password lama</label>' +
      '<input type="password" id="pw_cur" autocomplete="current-password"></div>' +
      '<div class="pk-edit-field"><label>Password baru (min. 6 karakter)</label>' +
      '<input type="password" id="pw_new" autocomplete="new-password"></div>' +
      '<div class="pk-edit-field"><label>Ulangi password baru</label>' +
      '<input type="password" id="pw_new2" autocomplete="new-password"></div>' +
      '<div class="pk-edit-actions">' +
      '<button type="button" class="btn" id="pw_go">Ganti Password</button>' +
      '<button type="button" class="btn btn-ghost" id="pw_cancel">Batal</button>' +
      "</div>" +
      '<p class="sec-sub pk-edit-msg"></p>' +
      "</div>"
    );
    document.getElementById("pw_cancel").onclick = closeOverlay;
    document.getElementById("pw_go").onclick = function () {
      var msg = document.querySelector(".pk-edit-msg");
      var cur = document.getElementById("pw_cur").value;
      var nw = document.getElementById("pw_new").value;
      var c2 = document.getElementById("pw_new2").value;
      if (!cur || !nw) { msg.textContent = "Isi password lama dan baru."; return; }
      msg.textContent = "Menyimpan…";
      fetch("api/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current: cur, password: nw, confirm: c2 })
      }).then(function (r) {
        return r.json().then(function (d) { return { ok: r.ok, d: d }; });
      }).then(function (r2) {
        if (r2.ok) {
          msg.textContent = "✅ Password diganti. Keluar lalu login pakai password baru…";
          setTimeout(function () {
            fetch("api/logout", { method: "POST" }).then(function () {
              window.location.href = "/login";
            });
          }, 1000);
        } else {
          msg.textContent = "❌ " + ((r2.d && r2.d.error) || "Gagal menyimpan.");
        }
      }).catch(function () { msg.textContent = "❌ API tidak tersedia."; });
    };
  }

  function ensureOverlay() {
    var o = document.getElementById("pk-edit-overlay");
    if (o) return o;
    o = document.createElement("div");
    o.id = "pk-edit-overlay";
    o.className = "pk-edit-overlay";
    o.innerHTML =
      '<div class="pk-edit-box">' +
      '<button type="button" class="pk-modal-close pk-edit-close" aria-label="Tutup">&times;</button>' +
      '<div class="pk-edit-body"></div>' +
      "</div>";
    o.addEventListener("click", function (e) { if (e.target === o) closeOverlay(); });
    o.querySelector(".pk-edit-close").onclick = closeOverlay;
    document.body.appendChild(o);
    return o;
  }
  function closeOverlay() {
    var o = document.getElementById("pk-edit-overlay");
    if (o) o.classList.remove("open");
    document.body.style.overflow = "";
  }
  function openOverlay(html) {
    var o = ensureOverlay();
    o.querySelector(".pk-edit-body").innerHTML = html;
    o.classList.add("open");
    document.body.style.overflow = "hidden";
    return o;
  }

  function editBtns() {
    host.querySelectorAll(".pk-card").forEach(function (card) {
      if (card.querySelector(".pk-card-edit")) return;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "pk-card-edit";
      b.textContent = "✏️";
      b.title = "Ubah produk ini";
      var p = items.find(function (x) { return x.model === card.getAttribute("data-model"); });
      b.onclick = function (ev) { ev.stopPropagation(); openEdit(p, files); };
      card.appendChild(b);
    });
  }

  function inputRow(label, id, val, opts) {
    opts = opts || {};
    var inp;
    if (opts.textarea) {
      inp = '<textarea id="' + id + '" rows="' + (opts.rows || 4) + '">' + escHtml(String(val == null ? "" : val)) + "</textarea>";
    } else if (opts.select) {
      inp = '<select id="' + id + '"></select>';
    } else {
      inp = '<input id="' + id + '" type="' + (opts.type || "text") + '" value="' + escHtml(String(val == null ? "" : val)) + '">';
    }
    return '<label>' + label + inp + "</label>";
  }
  function escHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // resize gambar client-side biar upload ringan (maks ~1600px, jpeg 0.86)
  function resizeImage(file, maxDim) {
    return new Promise(function (resolve, reject) {
      if (!/^image\//.test(file.type)) return reject(new Error("bukan gambar"));
      var reader = new FileReader();
      reader.onload = function (e) {
        var img = new Image();
        img.onload = function () {
          var scale = Math.min(1, maxDim / Math.max(img.width, img.height));
          var w = Math.max(1, Math.round(img.width * scale));
          var h = Math.max(1, Math.round(img.height * scale));
          var cv = document.createElement("canvas");
          cv.width = w; cv.height = h;
          cv.getContext("2d").drawImage(img, 0, 0, w, h);
          var q = 0.86;
          var b64 = cv.toDataURL("image/jpeg", q).split(",")[1];
          while (b64.length > 5000000 && q > 0.3) {
            q -= 0.1;
            b64 = cv.toDataURL("image/jpeg", q).split(",")[1];
          }
          resolve({ data: b64 });
        };
        img.onerror = function () { reject(new Error("gambar rusak")); };
        img.src = e.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function openEdit(p, files) {
    var isNew = !p;
    var base = p || {};
    var fotos = (p ? (p.foto_list || []).slice() : []);
    var optHtml = '<option value="">(pakai foto otomatis)</option>';
    var prefix = (base.model || "").toLowerCase() + "__";
    var matches = (files || []).filter(function (f) { return f.name.toLowerCase().indexOf(prefix) === 0; });
    matches.forEach(function (f) {
      var sel = (base.foto === f.url || fotos[0] === f.url) ? " selected" : "";
      optHtml += '<option value="' + f.url + '"' + sel + ">" + f.name + "</option>";
    });
    openOverlay(
      '<h3 class="pk-modal-title">' + (isNew ? "Tambah Produk Baru" : "Ubah Produk — " + escHtml(p.model)) + "</h3>" +
      '<form id="pk-edit-form" class="pk-edit-form">' +
      inputRow("Nama model (wajib)", "f_model", base.model) +
      inputRow("Kategori", "f_kategori", base.kategori) +
      inputRow("Group", "f_group", base.group) +
      inputRow("Varian / warna (pisah koma)", "f_varian", (base.varian || []).join(", ")) +
      '<div class="pk-edit-cols">' +
      inputRow("Kapasitas gross (L)", "f_gross", base.kapasitas_gross, { type: "number" }) +
      inputRow("Kapasitas nett (L)", "f_nett", base.kapasitas_nett, { type: "number" }) +
      "</div>" +
      inputRow("Rentang kapasitas", "f_range", base.range) +
      inputRow("Material pintu", "f_material", base.material) +
      '<div class="pk-edit-cols">' +
      inputRow("Daya listrik (W)", "f_daya", base.daya_watt) +
      inputRow("Garansi (tahun)", "f_garansi", base.garansi_tahun) +
      "</div>" +
      inputRow("Flags (pisah koma, mis. Inverter, Entry)", "f_flags", (base.flags || []).join(", ")) +
      inputRow("Seri", "f_serie", base.serie) +
      inputRow("Harga pasar (Rp, angka saja)", "f_harga", base.harga_idr) +
      buildFotoSlotsHtml(base, files) +
      inputRow("Fitur unggulan (1 poin per baris)", "f_fitur", (base.fitur || []).join("\n"), { textarea: true, rows: 6 }) +
      inputRow("Keunggulan / deskripsi", "f_benefit", base.benefit, { textarea: true, rows: 5 }) +
      '<div class="pk-edit-actions">' +
      '<button type="button" class="btn" id="pk-edit-save">💾 Simpan</button>' +
      '<button type="button" class="btn btn-ghost" id="pk-edit-cancel">Batal</button>' +
      "</div>" +
      '<p class="sec-sub pk-edit-msg"></p>' +
      "</form>"
    );
    setupFotoSlots(p, files);
    document.getElementById("pk-edit-cancel").onclick = closeOverlay;

    document.getElementById("pk-edit-save").onclick = function () {
      var msg = document.querySelector(".pk-edit-msg");
      var np = {};
      if (!isNew) Object.keys(p).forEach(function (k) { if (k !== "foto_list") np[k] = p[k]; });
      np.model = document.getElementById("f_model").value.trim();
      np.kategori = document.getElementById("f_kategori").value.trim();
      np.group = document.getElementById("f_group").value.trim();
      np.varian = document.getElementById("f_varian").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      np.kapasitas_gross = numOrNull(document.getElementById("f_gross").value);
      np.kapasitas_nett = numOrNull(document.getElementById("f_nett").value);
      np.range = document.getElementById("f_range").value.trim();
      np.material = document.getElementById("f_material").value.trim();
      np.daya_watt = document.getElementById("f_daya").value.trim();
      np.garansi_tahun = document.getElementById("f_garansi").value.trim();
      np.flags = document.getElementById("f_flags").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      np.serie = document.getElementById("f_serie").value.trim();
      np.harga_idr = numOrNull(document.getElementById("f_harga").value);
      // foto: kumpulkan slot terisi (maks 5, urut sesuai slot)
      var slots = [];
      for (var si = 0; si < 5; si++) {
        var sv = document.getElementById("f_foto_" + si).value;
        if (sv && slots.indexOf(sv) === -1) slots.push(sv);
      }
      if (slots.length) { np.foto = slots[0]; np.foto_list = slots; }
      else { delete np.foto; delete np.foto_list; }
      // fitur unggulan: 1 baris = 1 poin
      var flines = document.getElementById("f_fitur").value.split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
      np.fitur = flines.length ? flines : null;
      np.benefit = document.getElementById("f_benefit").value.trim();
      if (!np.model) { msg.textContent = "❌ Nama model wajib diisi."; return; }
      if (isNew && items.some(function (x) { return x.model === np.model; })) {
        msg.textContent = "❌ Model sudah ada di katalog. Pakai nama lain atau edit yang lama.";
        return;
      }
      msg.textContent = "Menyimpan…";
      var next = isNew ? items.concat([np]) : items.map(function (x) { return x.model === p.model ? np : x; });
      fetch("api/produk", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next)
      }).then(function (r) {
        if (r.ok) {
          msg.textContent = "✅ Tersimpan. Memuat ulang…";
          setTimeout(function () { location.reload(); }, 600);
        } else if (r.status === 401) {
          msg.textContent = "❌ Sesi login habis. Login ulang untuk mengubah.";
        } else {
          msg.textContent = "❌ Gagal simpan (" + r.status + ").";
        }
      }).catch(function () { msg.textContent = "❌ API tidak tersedia."; });
    };
  }

  function buildFotoSlotsHtml(base, files) {
    var slotVals = [];
    if (base && base.model) {
      var fl = (base.foto_list || []).slice();
      var primary = base.foto || fl[0];
      slotVals = [primary].concat(fl.filter(function (u) { return u !== primary; })).slice(0, 5);
    }
    var h = '<div class="pk-foto-slots">';
    for (var i = 0; i < 5; i++) {
      var selV = slotVals[i] || "";
      var opts = '<option value="">(kosong)</option>';
      (files || []).forEach(function (f) {
        var s = f.url === selV ? " selected" : "";
        opts += '<option value="' + f.url + '"' + s + ">" + f.name + "</option>";
      });
      h +=
        '<div class="pk-foto-slot">' +
        '<span class="pk-foto-slot-label">' + (i === 0 ? "Foto 1 (utama)" : "Foto " + (i + 1)) + "</span>" +
        '<select id="f_foto_' + i + '" class="pk-foto-sel">' + opts + "</select>" +
        '<div class="pk-foto-slot-up">' +
        '<input type="file" id="f_up' + i + '" accept="image/*" hidden>' +
        '<button type="button" class="btn btn-sec" data-slot="' + i + '">Upload ke slot ini</button>' +
        "</div></div>";
    }
    return h + "</div>";
  }

  function setupFotoSlots(p, files) {
    for (var i = 0; i < 5; i++) {
      var upBtn = document.querySelector('[data-slot="' + i + '"]');
      if (!upBtn) continue;
      var fi = document.getElementById("f_up" + i);
      var sel = document.getElementById("f_foto_" + i);
      (function (input, select, idx) {
        upBtn.onclick = function () { input.click(); };
        input.addEventListener("change", function (ev) {
          var file = ev.target.files && ev.target.files[0];
          if (!file) return;
          resizeImage(file, 1600).then(function (res) {
            var fn = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");
            fetch("api/foto", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: fn, data: res.data })
            }).then(function (r) {
              return r.json().then(function (d) { return { ok: r.ok, d: d }; });
            }).then(function (r2) {
              var msg = document.getElementById("pk-edit-up-msg");
              if (r2.ok && r2.d.url) {
                var nm = r2.d.url.split("/").pop().split("?")[0];
                if (!window.MTMS_MANIFEST.some(function (m) { return m.url === r2.d.url; })) {
                  window.MTMS_MANIFEST.push({ name: nm, url: r2.d.url });
                }
                refreshFotoDropdowns();
                select.value = r2.d.url;
                if (msg) msg.textContent = "✅ Foto terupload ke slot ini.";
              } else if (msg) {
                msg.textContent = "❌ Upload gagal: " + ((r2.d && r2.d.error) || "?");
              }
            }).catch(function () { var m = document.getElementById("pk-edit-up-msg"); if (m) m.textContent = "❌ API tidak tersedia."; });
          }).catch(function () { var m = document.getElementById("pk-edit-up-msg"); if (m) m.textContent = "❌ File bukan gambar."; });
        });
      })(fi, sel, i);
    }
  }

  function refreshFotoDropdowns() {
    for (var i = 0; i < 5; i++) {
      var sel = document.getElementById("f_foto_" + i);
      if (!sel) continue;
      var cur = sel.value;
      var opts = '<option value="">(kosong)</option>';
      window.MTMS_MANIFEST.forEach(function (f) {
        var s = f.url === cur ? " selected" : "";
        opts += '<option value="' + f.url + '"' + s + ">" + f.name + "</option>";
      });
      sel.innerHTML = opts;
      sel.value = cur;
    }
  }

  function numOrNull(v) {
    v = String(v).trim();
    if (!v) return null;
    var n = parseFloat(v.replace(/\./g, "").replace(/,/g, "."));
    return isNaN(n) ? null : n;
  }

  // expose untuk tombol Edit di modal (scope berbeda)
  window.__mtms_openEdit = function (p) { openEdit(p, window.MTMS_MANIFEST || files); };
  // pasang tombol edit di kartu (dipanggil tiap render lewat hook global)
  window.__mtms_after_render = editBtns;
  editBtns();
}
