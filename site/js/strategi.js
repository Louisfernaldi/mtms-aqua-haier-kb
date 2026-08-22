/* Tiket 08 - halaman strategi CEO. Semua angka dirender dari strategi.json (nol hardcode). */
(function () {
  "use strict";

  var DATA_URL = "data/insight/strategi.json";
  var WARNA_AQUA = "#087fac";
  var WARNA_LAIN = "#df6b3f";

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function fmtPct(v) {
    return (v * 100).toFixed(1).replace(".", ",") + "%";
  }

  function chipSumber(container, sumber, periode) {
    var row = container.querySelector(".source-row");
    if (!row || !sumber) return;
    row.textContent = "";
    row.appendChild(el("span", "chip", "Sumber: " + sumber));
    if (periode) row.appendChild(el("span", "chip chip-dim", periode));
  }

  function renderPosisi(d, periode) {
    var pn = d.posisi_nasional;
    var cards = document.getElementById("posisiCards");
    cards.textContent = "";
    [
      ["Share unit", fmtPct(pn.unit_share), "peringkat #" + pn.unit_rank + " nasional"],
      ["Share nilai", fmtPct(pn.value_share), "peringkat #" + pn.value_rank + " nasional"],
      ["Indeks ASP", String(pn.asp_index).replace(".", ","), "nilai/unit; <1 = harga di bawah pasar"]
    ].forEach(function (c) {
      var card = el("div", "stat-card");
      card.appendChild(el("p", "stat-label", c[0]));
      card.appendChild(el("p", "stat-value", c[1]));
      card.appendChild(el("p", "stat-note", c[2]));
      cards.appendChild(card);
    });
    document.getElementById("posisiCount").textContent =
      "AQUA unit #" + pn.unit_rank + ", nilai #" + pn.value_rank;

    drawBarChart("chartUnit", pn.top5_unit.map(function (b) {
      return [b.brand, +(b.share * 100).toFixed(1), b.brand === "AQUA" ? WARNA_AQUA : WARNA_LAIN];
    }), { suffix: "%" });
    drawBarChart("chartValue", pn.top5_value.map(function (b) {
      return [b.brand, +(b.share * 100).toFixed(1), b.brand === "AQUA" ? WARNA_AQUA : WARNA_LAIN];
    }), { suffix: "%" });

    var panel = document.getElementById("posisiCards").closest(".panel");
    chipSumber(panel, pn.sumber, periode);
  }

  function renderRegion(d, periode) {
    var rows = d.region;
    document.getElementById("regionCount").textContent = rows.length + " region";
    drawBarChart("chartRegion", rows.map(function (r) {
      return [r.region, +(r.aqua_share * 100).toFixed(1), WARNA_AQUA];
    }), { suffix: "%", height: 360, subLabel: rows.map(function (r) { return "juara: " + r.penguasa.brand; }) });

    var tbl = document.getElementById("regionTable");
    tbl.textContent = "";
    var table = el("table");
    var thead = el("thead");
    var hr = el("tr");
    ["Region", "AQUA", "Penguasa region"].forEach(function (h) { hr.appendChild(el("th", null, h)); });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = el("tbody");
    rows.forEach(function (r) {
      var tr = el("tr");
      tr.appendChild(el("td", null, r.region));
      tr.appendChild(el("td", "num", fmtPct(r.aqua_share)));
      tr.appendChild(el("td", null, r.penguasa.brand + " (" + fmtPct(r.penguasa.share) + ")"));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tbl.appendChild(table);

    var panel = document.getElementById("regionTable").closest(".panel");
    chipSumber(panel, rows[0] && rows[0].sumber ? rows[0].sumber.split("#")[0].replace("site/data/insight/", "") : "", periode);
  }

  function renderKelas(d, periode) {
    var rows = d.kelas_harga;
    document.getElementById("kelasCount").textContent = rows.length + " kelas harga";
    drawBarChart("chartKelas", rows.map(function (k) {
      return [k.kelas.replace(" MIL IDR", ""), +(k.aqua_share * 100).toFixed(1), WARNA_AQUA];
    }), { suffix: "%", height: 380 });

    var panel = document.getElementById("chartKelas").closest(".panel");
    chipSumber(panel, rows[0] && rows[0].sumber ? rows[0].sumber.split("#")[0].replace("site/data/insight/", "") : "", periode);
  }

  function renderTipe(d, periode) {
    var rows = d.tipe_pintu.filter(function (t) { return t.tipe !== "N.A."; });
    document.getElementById("tipeCount").textContent = rows.length + " tipe pintu";
    drawBarChart("chartTipe", rows.map(function (t) {
      return [t.tipe, +(t.aqua_share * 100).toFixed(1), t.aqua_share === 0 ? "#b9483a" : WARNA_AQUA];
    }), { suffix: "%", height: 340 });

    var panel = document.getElementById("chartTipe").closest(".panel");
    chipSumber(panel, rows[0] && rows[0].sumber ? rows[0].sumber.split("#")[0].replace("site/data/insight/", "") : "", periode);
  }

  function renderDilema(d, periode) {
    var body = document.getElementById("dilemaBody");
    body.textContent = "";
    d.dilema_dealer_b2c.paragraf.forEach(function (p) {
      body.appendChild(el("p", "narasi-paragraf", p));
    });
    var panel = body.closest(".panel");
    chipSumber(panel, d.dilema_dealer_b2c.sumber.split("#")[0].replace("site/data/insight/", ""), periode);
  }

  function renderRekomendasi(d) {
    var list = document.getElementById("rekomendasiList");
    list.textContent = "";
    d.rekomendasi.forEach(function (r) {
      var kartu = el("article", "rekomendasi-card tingkat-" + r.tingkat.toLowerCase());
      kartu.appendChild(el("span", "tingkat-badge", r.tingkat));
      kartu.appendChild(el("h3", null, r.judul));
      kartu.appendChild(el("p", null, r.isi));
      if (r.sumber) kartu.appendChild(el("span", "chip chip-mini", r.sumber));
      list.appendChild(kartu);
    });
    document.getElementById("rekomendasiCount").textContent = d.rekomendasi.length + " rekomendasi";
  }

  function main() {
    fetch(DATA_URL)
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (d) {
        var periode = d.meta.periode;
        document.getElementById("strategiSummary").textContent =
          "Periode data " + periode + " - narasi analis, angka terisi mesin dari " + d.meta.sumber;
        document.getElementById("generatedAt").textContent = d.meta.digenerate;
        renderPosisi(d, periode);
        renderRegion(d, periode);
        renderKelas(d, periode);
        renderTipe(d, periode);
        renderDilema(d, periode);
        renderRekomendasi(d);
      })
      .catch(function (e) {
        document.getElementById("strategiSummary").textContent = "Gagal memuat data strategi: " + e.message;
      });
  }

  main();
})();
