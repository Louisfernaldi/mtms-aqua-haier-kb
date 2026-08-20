// proses.js — Halaman Proses: timeline launch bernomor + kartu latihan Excel.
// Baca data dari window.MTMS_DATA (data.js) dulu, fallback fetch file JSON.

function kbLoad(name) {
  if (window.MTMS_DATA && window.MTMS_DATA.knowledge && window.MTMS_DATA.knowledge[name]) {
    return Promise.resolve(window.MTMS_DATA.knowledge[name]);
  }
  return fetch("data/knowledge/" + name).then(function (r) {
    return r.json();
  });
}

// [[x]] di data JSON jadi chip (badge angka penting).
function chipify(txt) {
  return txt.replace(/\[\[(.*?)\]\]/g, '<span class="chip">$1</span>');
}

function statusBadge(status) {
  var label = { "selesai": "Selesai", "in-progress": "In Progress", "belum": "Belum" }[status] || status;
  var cls = { "selesai": "selesai", "in-progress": "in-progress", "belum": "belum" }[status] || "belum";
  return '<span class="tl-badge ' + cls + '">' + label + "</span>";
}

function renderTimeline(hostId, name) {
  kbLoad(name).then(function (j) {
    if (!j || !j.langkah) return;
    var host = document.getElementById(hostId);
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
    var ol = document.createElement("ol");
    ol.className = "tl-list";
    j.langkah.forEach(function (s) {
      var li = document.createElement("li");
      li.className = "tl-step";
      var num = document.createElement("span");
      num.className = "tl-num";
      num.textContent = s.urut;
      var body = document.createElement("div");
      body.className = "tl-body";
      var title = document.createElement("div");
      title.className = "tl-title";
      title.innerHTML = "<b>" + esc(s.judul) + "</b>" + statusBadge(s.status);
      var pic = document.createElement("div");
      pic.className = "tl-pic";
      pic.innerHTML = "PIC: <b>" + (s.pic ? esc(s.pic) : "-") + "</b>";
      body.appendChild(title);
      body.appendChild(pic);
      if (s.detail) {
        var det = document.createElement("p");
        det.className = "tl-detail";
        det.textContent = s.detail;
        body.appendChild(det);
      }
      li.appendChild(num);
      li.appendChild(body);
      ol.appendChild(li);
    });
    sec.appendChild(ol);
    var kunci = null;
    (j.fakta || []).forEach(function (f) {
      if (f.judul.indexOf("Kunci") !== -1) kunci = f;
    });
    if (kunci) {
      var kc = document.createElement("div");
      kc.className = "card kunci-card";
      var kh = document.createElement("h3");
      kh.textContent = kunci.judul;
      var kp = document.createElement("p");
      kp.textContent = kunci.isi;
      kc.appendChild(kh);
      kc.appendChild(kp);
      sec.appendChild(kc);
    }
    host.appendChild(sec);
  });
}

function renderTugas(hostId, name) {
  kbLoad(name).then(function (j) {
    if (!j) return;
    var host = document.getElementById(hostId);
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
    var grid = document.createElement("div");
    grid.className = "grid";
    j.fakta.forEach(function (f) {
      var card = document.createElement("div");
      card.className = "card tugas-card";
      var h3 = document.createElement("h3");
      h3.innerHTML = '<span class="fakta-ico">' + faktaEmoji(f.judul, f.isi) + "</span>" + f.judul;
      card.appendChild(h3);
      if (f.poin && f.poin.length) {
        var ul = document.createElement("ul");
        ul.className = "tugas-poin";
        f.poin.forEach(function (p) {
          var li = document.createElement("li");
          li.innerHTML = chipify(esc(p));
          ul.appendChild(li);
        });
        card.appendChild(ul);
      } else {
        var pl = document.createElement("p");
        pl.textContent = f.isi;
        card.appendChild(pl);
      }
      var s = document.createElement("span");
      s.className = "src";
      s.textContent = "Sumber: " + f.sumber;
      card.appendChild(s);
      grid.appendChild(card);
    });
    sec.appendChild(grid);
    host.appendChild(sec);
  });
}
