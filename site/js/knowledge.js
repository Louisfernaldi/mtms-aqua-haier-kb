function faktaEmoji(judul, isi) {
  var t = (judul + " " + isi).toLowerCase();
  var map = [
    ["kulkas", "🧊"], ["refrigerator", "🧊"], ["freezer", "❄️"], ["dingin", "❄️"],
    ["tv", "📺"], ["televisi", "📺"],
    ["air", "💧"], ["water", "💧"], ["dispenser", "💧"], ["pemanas", "💧"],
    ["garansi", "🛡️"], ["kompresor", "🛡️"],
    ["inverter", "⚡"], ["daya", "⚡"], ["hemat listrik", "⚡"],
    ["harga", "💰"], ["segmen", "💰"], ["modal", "💰"],
    ["kompetitor", "⚔️"], ["benchmark", "⚔️"], ["midea", "⚔️"], ["sharp", "⚔️"], ["polytron", "⚔️"],
    ["pangsa", "📊"], ["market share", "📊"], ["gfx", "📊"], ["gfk", "📊"],
    ["dealer", "🤝"], ["support", "🤝"],
    ["latihan", "📝"], ["excel", "📝"], ["tugas", "📝"], ["soal", "📝"],
    ["launch", "🚀"], ["peluncuran", "🚀"], ["rilis", "🚀"],
    ["kode", "🔤"], ["seri", "🔤"], ["model", "🔤"],
    ["brand", "🏷️"], ["merek", "🏷️"], ["global", "🌍"], ["dunia", "🌍"],
    ["benefit", "🎁"], ["keunggulan", "🎁"], ["fitur", "🎁"],
    ["tv", "📺"]
  ];
  for (var i = 0; i < map.length; i++) {
    if (t.indexOf(map[i][0]) !== -1) return map[i][1];
  }
  return "📄";
}

function renderKb(targetId, files) {
  var host = document.getElementById(targetId);
  if (!host) return;
  Promise.all(
    files.map(function (f) {
      if (window.MTMS_DATA && window.MTMS_DATA.knowledge && window.MTMS_DATA.knowledge[f]) {
        return Promise.resolve(window.MTMS_DATA.knowledge[f]);
      }
      return fetch("data/knowledge/" + f)
        .then(function (r) {
          return r.json();
        })
        .catch(function () {
          return null;
        });
    })
  ).then(function (list) {
    list.forEach(function (j) {
      if (!j) return;
      var sec = document.createElement("section");
      sec.className = "kb-sec";
      var h = document.createElement("h2");
      h.className = "sec";
      h.textContent = j.kategori;
      var sub = document.createElement("p");
      sub.className = "sec-sub";
      sub.textContent = j.deskripsi;
      sec.appendChild(h);
      sec.appendChild(sub);
      if (j.visual && (j.visual.kode || j.visual.subkategori || j.visual.level || j.visual.material || j.visual.komponen)) {
        var vwrap = document.createElement("div");
        vwrap.className = "ik-visual";
        vwrap.innerHTML = ikVisual(j.visual);
        sec.appendChild(vwrap);
      }
      var grid = document.createElement("div");
      grid.className = "grid";
      j.fakta.forEach(function (f) {
        var card = document.createElement("div");
        card.className = "card";
        var h3 = document.createElement("h3");
        h3.innerHTML = '<span class="fakta-ico">' + faktaEmoji(f.judul, f.isi) + "</span>" + f.judul;
        var p = document.createElement("p");
        p.textContent = f.isi;
        var s = document.createElement("span");
        s.className = "src";
        s.textContent = "Sumber: " + f.sumber;
        card.appendChild(h3);
        card.appendChild(p);
        card.appendChild(s);
        grid.appendChild(card);
      });
      sec.appendChild(grid);
      host.appendChild(sec);
    });
  });
}

/* ==== Visual induksi kulkas (Tiket H3): render "visual" di atas kartu fakta ==== */
function ikEsc(s) {
  var d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function ikVisual(v) {
  var h = "";
  if (v.kode && v.kode.length) h += ikKode(v.kode);
  if (v.subkategori && v.subkategori.length) h += ikSubkategori(v.subkategori);
  if ((v.level && v.level.length) || (v.material && v.material.length)) h += ikLevelMaterial(v.level, v.material);
  if (v.komponen && v.komponen.length) h += ikKomponen(v.komponen);
  return h;
}

function ikKode(kodes) {
  var h = '<div class="ik-block"><h3 class="ik-title">Cara Baca Kode Produk</h3>';
  kodes.forEach(function (ex) {
    if (!ex || !ex.segmen || !ex.segmen.length) return;
    h += '<div class="ik-kode"><div class="ik-kode-row">';
    ex.segmen.forEach(function (s) {
      h += '<div class="ik-seg"><span class="ik-seg-txt" style="background:' + ikEsc(s.warna || "#64748b") + '">' +
        ikEsc(s.segmen) + "</span><span class=\"ik-seg-lbl\">" + ikEsc(s.label || "") + "</span></div>";
    });
    h += "</div>";
    if (ex.keterangan) h += '<p class="ik-kode-note">' + ikEsc(ex.keterangan) + "</p>";
    h += "</div>";
  });
  h += "</div>";
  return h;
}

function ikFridge(v) {
  var map = {
    sb: '<i class="f"></i>',
    se: '<i class="f-row"><i class="f"></i><i class="f"></i></i>',
    td: '<i class="f-row"><i class="f"></i><i class="f"></i></i><i class="f-row"><i class="f"></i><i class="f"></i></i>',
    tm: '<i class="f freezer"></i><i class="f"></i>',
    bm: '<i class="f"></i><i class="f freezer"></i>'
  };
  return '<span class="ik-fridge" aria-hidden="true">' + (map[v] || map.sb) + "</span>";
}

function ikSubkategori(list) {
  var h = '<div class="ik-block"><h3 class="ik-title">Sub-kategori Kulkas</h3><div class="ik-sub-grid">';
  list.forEach(function (s) {
    h += '<div class="ik-sub">' + ikFridge(s.varian || "") +
      '<span class="ik-sub-kode">' + ikEsc(s.kode) + "</span>" +
      '<span class="ik-sub-nama">' + ikEsc(s.nama) + "</span>" +
      '<span class="ik-sub-desc">' + ikEsc(s.desc || "") + "</span></div>";
  });
  h += "</div></div>";
  return h;
}

function ikLevelMaterial(level, material) {
  var h = '<div class="ik-block"><h3 class="ik-title">Level &amp; Material Pintu</h3>';
  if (level && level.length) {
    h += '<div class="ik-lv-wrap"><span class="ik-grp-lbl">Level produk:</span>';
    level.forEach(function (l) {
      h += '<span class="ik-chip ik-lv" style="background:' + ikEsc(l.warna || "#64748b") + '">' +
        '<span class="ik-lv-code">' + ikEsc(l.kode) + "</span>" +
        (l.desc ? '<span class="ik-lv-desc">' + ikEsc(l.desc) + "</span>" : "") + "</span>";
    });
    h += "</div>";
  }
  if (material && material.length) {
    h += '<div class="ik-lv-wrap"><span class="ik-grp-lbl">Material pintu:</span>';
    material.forEach(function (m) {
      h += '<span class="ik-chip ik-mat" style="background:' + ikEsc(m.warna || "#64748b") + '">' +
        '<span class="ik-lv-code">' + ikEsc(m.nama) + "</span>" +
        (m.catatan ? '<span class="ik-lv-desc">' + ikEsc(m.catatan) + "</span>" : "") + "</span>";
    });
    h += "</div>";
  }
  h += '<p class="ik-kode-note">Level produk (S/A/B/Basic) dan material pintu (G = Glass / Metal) dari fakta "Level dan material pintu".</p>';
  h += "</div>";
  return h;
}

function ikKomponen(komp) {
  var cycle = ["Kompresor", "Kondensor", "Evaporator"];
  var cyc = [], sup = [];
  komp.forEach(function (k) {
    if (cycle.indexOf(k.nama) !== -1) cyc.push(k);
    else sup.push(k);
  });
  var h = '<div class="ik-block"><h3 class="ik-title">Siklus Pendinginan &amp; Komponen</h3>';
  h += '<div class="ik-cycle-row">';
  cyc.forEach(function (k, i) {
    h += '<div class="ik-komp"><span class="ik-komp-nama">' + ikEsc(k.nama) + "</span>" +
      '<span class="ik-komp-peran">' + ikEsc(k.peran || "") + "</span></div>";
    h += '<span class="ik-arrow" aria-hidden="true">&rarr;</span>';
  });
  h += '<span class="ik-arrow-back">kembali ke kompresor</span>';
  h += "</div>";
  if (sup.length) {
    h += '<div class="ik-comp-pendukung"><span class="ik-grp-lbl">Komponen pendukung:</span><div class="ik-cycle-row">';
    sup.forEach(function (k) {
      h += '<div class="ik-komp"><span class="ik-komp-nama">' + ikEsc(k.nama) + "</span>" +
        '<span class="ik-komp-peran">' + ikEsc(k.peran || "") + "</span></div>";
    });
    h += "</div></div>";
  }
  h += '<p class="ik-kode-note">Urutan siklus: kompresor &rarr; kondensor &rarr; evaporator, lalu kembali ke kompresor (fakta "Komponen utama kulkas").</p>';
  h += "</div>";
  return h;
}
