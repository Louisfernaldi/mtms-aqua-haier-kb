(function () {
  "use strict";

  var DATA_URL = "data/insight/gfk-market-share.json";
  var OTHER_COLORS = [
    "#df6b3f", "#7357b5", "#33845d", "#d09216", "#c44f87",
    "#4d72c5", "#8b6536", "#14999b", "#98565f", "#667735",
    "#8051a8", "#b96d3c", "#467a86", "#966a91", "#596fa7",
    "#a45435", "#247e96", "#7e6b29", "#a33f62", "#4f7780"
  ];
  var state = {
    payload: null,
    colors: {},
    priceClass: "",
    refType: ""
  };
  var percent = new Intl.NumberFormat("id-ID", {
    style: "percent",
    maximumFractionDigits: 2
  });
  var count = new Intl.NumberFormat("id-ID");

  function byId(id) {
    return document.getElementById(id);
  }

  function hasOwn(object, key) {
    return Object.prototype.hasOwnProperty.call(object, key);
  }

  function shareEntries(shareMap) {
    return Object.entries(shareMap).sort(function (left, right) {
      return right[1] - left[1] || left[0].localeCompare(right[0], "id", {
        sensitivity: "base"
      });
    });
  }

  function isShareMap(value) {
    return value && typeof value === "object" && !Array.isArray(value) &&
      Object.keys(value).length > 0 && Object.values(value).every(function (share) {
        return typeof share === "number" && Number.isFinite(share) && share >= 0;
      });
  }

  function isNestedShareMap(value) {
    return value && typeof value === "object" && !Array.isArray(value) &&
      Object.keys(value).length > 0 && Object.values(value).every(isShareMap);
  }

  function validatePayload(payload) {
    return payload && payload.meta &&
      typeof payload.meta.periode === "string" && payload.meta.periode.length > 0 &&
      typeof payload.meta.sumber_file === "string" &&
      isShareMap(payload.share_unit_nasional) &&
      isShareMap(payload.share_value_nasional) &&
      isNestedShareMap(payload.share_unit_per_region) &&
      isNestedShareMap(payload.share_per_price_class) &&
      isNestedShareMap(payload.ref_type_breakdown);
  }

  function uniqueBrands(payload) {
    var brands = new Set();
    [payload.share_unit_nasional, payload.share_value_nasional].forEach(function (shareMap) {
      Object.keys(shareMap).forEach(function (brand) { brands.add(brand); });
    });
    [payload.share_unit_per_region, payload.share_per_price_class, payload.ref_type_breakdown]
      .forEach(function (group) {
        Object.values(group).forEach(function (shareMap) {
          Object.keys(shareMap).forEach(function (brand) { brands.add(brand); });
        });
      });
    return Array.from(brands).sort(function (left, right) {
      var difference = (payload.share_unit_nasional[right] || 0) -
        (payload.share_unit_nasional[left] || 0);
      return difference || left.localeCompare(right, "id", { sensitivity: "base" });
    });
  }

  function buildColorMap(brands) {
    var colors = {};
    var otherIndex = 0;
    brands.forEach(function (brand) {
      if (brand === "AQUA") {
        colors[brand] = "#087fac";
      } else {
        colors[brand] = OTHER_COLORS[otherIndex % OTHER_COLORS.length];
        otherIndex += 1;
      }
    });
    return colors;
  }

  function populateFilter(select, values) {
    var fragment = document.createDocumentFragment();
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      fragment.appendChild(option);
    });
    select.replaceChildren(fragment);
    select.disabled = !values.length;
    return values.length ? values[0] : "";
  }

  function createSwatch(color) {
    var swatch = document.createElement("i");
    swatch.className = "legend-swatch";
    swatch.style.setProperty("--swatch", color);
    return swatch;
  }

  function createBarLine(label, value, color) {
    var line = document.createElement("div");
    line.className = "share-line";

    var series = document.createElement("span");
    series.className = "series-label";
    series.textContent = label;

    var track = document.createElement("span");
    track.className = "bar-track";
    var fill = document.createElement("span");
    fill.className = "bar-fill";
    fill.style.setProperty("--share", String(value));
    fill.style.setProperty("--bar-color", color);
    track.appendChild(fill);

    var valueLabel = document.createElement("strong");
    valueLabel.className = "share-value";
    valueLabel.textContent = percent.format(value);

    line.setAttribute("aria-label", label + " " + percent.format(value));
    line.appendChild(series);
    line.appendChild(track);
    line.appendChild(valueLabel);
    return line;
  }

  function renderNational() {
    var unitMap = state.payload.share_unit_nasional;
    var valueMap = state.payload.share_value_nasional;
    var brands = Array.from(new Set(Object.keys(unitMap).concat(Object.keys(valueMap))))
      .sort(function (left, right) {
        return (unitMap[right] || 0) - (unitMap[left] || 0) ||
          left.localeCompare(right, "id", { sensitivity: "base" });
      });
    var fragment = document.createDocumentFragment();

    brands.forEach(function (brand) {
      var row = document.createElement("article");
      row.className = "brand-row";
      if (brand === "AQUA") row.classList.add("is-aqua");

      var name = document.createElement("h3");
      name.textContent = brand;
      var bars = document.createElement("div");
      bars.className = "brand-measures";
      if (hasOwn(unitMap, brand)) {
        bars.appendChild(createBarLine("Unit", unitMap[brand], "var(--unit-color)"));
      }
      if (hasOwn(valueMap, brand)) {
        bars.appendChild(createBarLine("Value", valueMap[brand], "var(--value-color)"));
      }
      row.appendChild(name);
      row.appendChild(bars);
      fragment.appendChild(row);
    });

    byId("nationalChart").replaceChildren(fragment);
    byId("nationalCount").textContent = count.format(brands.length) + " brand";
  }

  function renderRegionLegend(brands) {
    var fragment = document.createDocumentFragment();
    brands.forEach(function (brand) {
      var item = document.createElement("span");
      item.className = "brand-legend-item";
      item.appendChild(createSwatch(state.colors[brand]));
      item.appendChild(document.createTextNode(brand));
      fragment.appendChild(item);
    });
    byId("regionLegend").replaceChildren(fragment);
  }

  function renderRegions() {
    var regionMaps = state.payload.share_unit_per_region;
    var regionNames = Object.keys(regionMaps);
    var brandSet = new Set();
    Object.values(regionMaps).forEach(function (shareMap) {
      Object.keys(shareMap).forEach(function (brand) { brandSet.add(brand); });
    });
    var brands = Array.from(brandSet).sort(function (left, right) {
      var national = state.payload.share_unit_nasional;
      return (national[right] || 0) - (national[left] || 0) ||
        left.localeCompare(right, "id", { sensitivity: "base" });
    });
    var fragment = document.createDocumentFragment();

    regionNames.forEach(function (regionName) {
      var row = document.createElement("article");
      row.className = "region-row";
      var label = document.createElement("h3");
      label.textContent = regionName;
      var stack = document.createElement("div");
      stack.className = "region-stack";
      stack.setAttribute("aria-label", "Pangsa unit " + regionName);

      shareEntries(regionMaps[regionName]).forEach(function (entry) {
        var brand = entry[0];
        var value = entry[1];
        var segment = document.createElement("span");
        segment.className = "region-segment";
        if (brand === "AQUA") segment.classList.add("is-aqua");
        segment.style.flexGrow = String(value);
        segment.style.setProperty("--bar-color", state.colors[brand]);
        segment.title = brand + " · " + percent.format(value);
        segment.setAttribute("aria-label", brand + " " + percent.format(value));
        stack.appendChild(segment);
      });

      row.appendChild(label);
      row.appendChild(stack);
      fragment.appendChild(row);
    });

    renderRegionLegend(brands);
    byId("regionChart").replaceChildren(fragment);
    byId("regionCount").textContent = count.format(regionNames.length) + " region · " +
      count.format(brands.length) + " brand";
  }

  function renderShareList(host, shareMap) {
    var fragment = document.createDocumentFragment();
    shareEntries(shareMap).forEach(function (entry) {
      var brand = entry[0];
      var value = entry[1];
      var row = document.createElement("div");
      row.className = "segment-brand-row";
      if (brand === "AQUA") row.classList.add("is-aqua");

      var name = document.createElement("span");
      name.className = "segment-brand-name";
      name.textContent = brand;
      var track = document.createElement("span");
      track.className = "bar-track";
      var fill = document.createElement("span");
      fill.className = "bar-fill";
      fill.style.setProperty("--share", String(value));
      fill.style.setProperty("--bar-color", state.colors[brand]);
      track.appendChild(fill);
      var valueLabel = document.createElement("strong");
      valueLabel.className = "share-value";
      valueLabel.textContent = percent.format(value);

      row.setAttribute("aria-label", brand + " " + percent.format(value));
      row.appendChild(name);
      row.appendChild(track);
      row.appendChild(valueLabel);
      fragment.appendChild(row);
    });
    host.replaceChildren(fragment);
  }

  function renderSegments() {
    var priceMap = state.payload.share_per_price_class[state.priceClass];
    var typeMap = state.payload.ref_type_breakdown[state.refType];
    renderShareList(byId("priceChart"), priceMap);
    renderShareList(byId("typeChart"), typeMap);
    byId("priceSelection").textContent = state.priceClass;
    byId("typeSelection").textContent = state.refType;
    byId("segmentCount").textContent = count.format(Object.keys(priceMap).length) +
      " brand di kelas harga · " + count.format(Object.keys(typeMap).length) +
      " brand di tipe pintu";
  }

  function setSourceRows(meta) {
    var jsonName = DATA_URL.split("/").pop();
    document.querySelectorAll("[data-json-source]").forEach(function (node) {
      node.textContent = jsonName;
    });
    document.querySelectorAll("[data-source-period]").forEach(function (node) {
      node.textContent = meta.periode;
    });
    byId("marketPeriod").textContent = meta.periode;
    byId("upstreamSource").textContent = meta.sumber_file;
  }

  function setSummary() {
    var payload = state.payload;
    byId("marketSummary").textContent = count.format(uniqueBrands(payload).length) +
      " brand · " + count.format(Object.keys(payload.share_unit_per_region).length) +
      " region · " + count.format(Object.keys(payload.share_per_price_class).length) +
      " kelas harga · " + count.format(Object.keys(payload.ref_type_breakdown).length) +
      " tipe pintu";
  }

  function bindControls() {
    byId("priceFilter").addEventListener("change", function (event) {
      state.priceClass = event.target.value;
      renderSegments();
    });
    byId("typeFilter").addEventListener("change", function (event) {
      state.refType = event.target.value;
      renderSegments();
    });
  }

  function showError(message) {
    var error = byId("loadError");
    error.hidden = false;
    error.textContent = "Data Peta Pasar gagal dimuat: " + message;
    byId("marketSummary").textContent = "Data pasar belum tersedia.";
    byId("priceFilter").disabled = true;
    byId("typeFilter").disabled = true;
  }

  fetch(DATA_URL, { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) throw new Error("respons sumber tidak berhasil");
      return response.json();
    })
    .then(function (payload) {
      if (!validatePayload(payload)) throw new Error("struktur JSON tidak valid");
      state.payload = payload;
      var brands = uniqueBrands(payload);
      state.colors = buildColorMap(brands);
      state.priceClass = populateFilter(
        byId("priceFilter"),
        Object.keys(payload.share_per_price_class)
      );
      state.refType = populateFilter(
        byId("typeFilter"),
        Object.keys(payload.ref_type_breakdown)
      );
      setSourceRows(payload.meta);
      setSummary();
      bindControls();
      renderNational();
      renderRegions();
      renderSegments();
    })
    .catch(function (error) {
      showError(error.message);
    });
}());
