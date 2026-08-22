(function () {
  "use strict";

  var DATA_URL = "data/insight/benchmark-harga.json";
  var SVG_NS = "http://www.w3.org/2000/svg";
  var COLORS = [
    "#087fac", "#e05d44", "#7357b5", "#3b8c62", "#d49a16", "#cb4c8b",
    "#4d75c5", "#8a673d", "#17a2a4", "#985861", "#657536", "#8051a8",
    "#bc7040", "#4c7b87", "#9b6d93", "#5e73a8"
  ];
  var state = {
    models: [],
    sourceFiles: [],
    brand: "",
    type: "",
    sortKey: "brand",
    sortDirection: 1
  };

  var currency = new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0
  });
  var number = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 });

  function byId(id) {
    return document.getElementById(id);
  }

  function svgEl(tag, attrs) {
    var node = document.createElementNS(SVG_NS, tag);
    Object.keys(attrs || {}).forEach(function (name) {
      node.setAttribute(name, attrs[name]);
    });
    return node;
  }

  function svgText(text, attrs) {
    var node = svgEl("text", attrs);
    node.textContent = text;
    return node;
  }

  function unique(values) {
    return Array.from(new Set(values)).sort(function (a, b) {
      return a.localeCompare(b, "id", { sensitivity: "base" });
    });
  }

  function populateFilter(select, values) {
    var first = select.options[0];
    select.replaceChildren(first);
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
  }

  function isModel(record) {
    return record && typeof record.brand === "string" &&
      typeof record.model === "string" &&
      typeof record.tipe_pintu === "string" &&
      typeof record.kapasitas_l === "number" &&
      (record.harga_rp === null || typeof record.harga_rp === "number") &&
      typeof record.sumber_file === "string";
  }

  function filteredModels() {
    return state.models.filter(function (record) {
      return (!state.brand || record.brand === state.brand) &&
        (!state.type || record.tipe_pintu === state.type);
    });
  }

  function compareValues(left, right, direction) {
    var leftMissing = left === null || typeof left === "undefined";
    var rightMissing = right === null || typeof right === "undefined";
    if (leftMissing || rightMissing) {
      if (leftMissing && rightMissing) return 0;
      return leftMissing ? 1 : -1;
    }
    if (typeof left === "number" && typeof right === "number") {
      return (left - right) * direction;
    }
    return String(left).localeCompare(String(right), "id", {
      numeric: true,
      sensitivity: "base"
    }) * direction;
  }

  function sortedModels(records) {
    return records.map(function (record, index) {
      return { record: record, index: index };
    }).sort(function (left, right) {
      var compared = compareValues(
        left.record[state.sortKey],
        right.record[state.sortKey],
        state.sortDirection
      );
      return compared || left.index - right.index;
    }).map(function (entry) {
      return entry.record;
    });
  }

  function appendCell(row, text, className) {
    var cell = document.createElement("td");
    if (className) cell.className = className;
    cell.textContent = text;
    row.appendChild(cell);
    return cell;
  }

  function appendMissingCell(row, className) {
    var cell = document.createElement("td");
    if (className) cell.className = className;
    var missing = document.createElement("em");
    missing.className = "missing-value";
    missing.textContent = "Belum ada";
    cell.appendChild(missing);
    row.appendChild(cell);
  }

  function setSourceRow(element, names) {
    element.replaceChildren();
    element.appendChild(document.createTextNode("Sumber: "));
    if (!names.length) {
      element.appendChild(document.createTextNode("tidak ada model dengan harga pada filter ini"));
      return;
    }
    names.forEach(function (name, index) {
      if (index) element.appendChild(document.createTextNode(" · "));
      var code = document.createElement("code");
      code.textContent = name;
      element.appendChild(code);
    });
  }

  function updateSortHeaders() {
    document.querySelectorAll("th[data-column]").forEach(function (header) {
      var active = header.dataset.column === state.sortKey;
      header.removeAttribute("aria-sort");
      if (active) {
        header.setAttribute(
          "aria-sort",
          state.sortDirection === 1 ? "ascending" : "descending"
        );
      }
    });
  }

  function renderTable(records) {
    var sorted = sortedModels(records);
    var body = byId("benchmarkRows");
    var fragment = document.createDocumentFragment();
    sorted.forEach(function (record) {
      var row = document.createElement("tr");
      appendCell(row, record.brand);
      appendCell(row, record.model, "model");
      appendCell(row, record.tipe_pintu);
      appendCell(row, number.format(record.kapasitas_l) + " L", "number");
      if (record.harga_rp === null) {
        appendMissingCell(row, "number");
        appendMissingCell(row, "number");
      } else {
        appendCell(row, currency.format(record.harga_rp), "number");
        appendCell(row, currency.format(record.harga_per_liter), "number");
      }
      appendCell(row, record.sumber_file, "source-cell");
      fragment.appendChild(row);
    });
    body.replaceChildren(fragment);
    byId("tableCount").textContent = number.format(sorted.length) + " model ditampilkan";
    setSourceRow(byId("tableSources"), state.sourceFiles);
    updateSortHeaders();
  }

  function niceStep(range, targetTicks) {
    if (!isFinite(range) || range <= 0) return 1;
    var rough = range / targetTicks;
    var power = Math.pow(10, Math.floor(Math.log10(rough)));
    var fraction = rough / power;
    var niceFraction = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10;
    return niceFraction * power;
  }

  function scaleDomain(values, includeZero) {
    var minValue = Math.min.apply(null, values);
    var maxValue = Math.max.apply(null, values);
    if (includeZero) minValue = 0;
    if (minValue === maxValue) {
      minValue = includeZero ? 0 : minValue * 0.9;
      maxValue = maxValue || 1;
      maxValue *= 1.1;
    }
    var step = niceStep(maxValue - minValue, 5);
    return {
      min: includeZero ? 0 : Math.floor(minValue / step) * step,
      max: Math.ceil(maxValue / step) * step,
      step: step
    };
  }

  function formatAxisPrice(value) {
    if (value >= 1000000) {
      return number.format(value / 1000000) + " jt";
    }
    if (value >= 1000) {
      return number.format(value / 1000) + " rb";
    }
    return number.format(value);
  }

  function colorMap(brands) {
    var colors = {};
    brands.forEach(function (brand, index) {
      colors[brand] = COLORS[index % COLORS.length];
    });
    return colors;
  }

  function renderLegend(brands, colors) {
    var legend = byId("scatterLegend");
    var fragment = document.createDocumentFragment();
    brands.forEach(function (brand) {
      var item = document.createElement("span");
      item.className = "legend-item";
      var swatch = document.createElement("span");
      swatch.className = "legend-swatch";
      swatch.style.setProperty("--swatch", colors[brand]);
      item.appendChild(swatch);
      item.appendChild(document.createTextNode(brand));
      fragment.appendChild(item);
    });
    legend.replaceChildren(fragment);
  }

  function renderScatter(records) {
    var host = byId("scatterChart");
    var points = records.filter(function (record) {
      return typeof record.harga_rp === "number";
    });
    var chartSources = unique(points.map(function (record) {
      return record.sumber_file;
    }));
    setSourceRow(byId("chartSources"), chartSources);
    byId("chartCount").textContent = number.format(points.length) + " model dengan harga";

    if (!points.length) {
      var empty = document.createElement("p");
      empty.className = "chart-empty";
      empty.textContent = "Belum ada harga yang bisa diplot untuk filter ini.";
      host.replaceChildren(empty);
      renderLegend([], {});
      return;
    }

    var width = 960;
    var height = 510;
    var pad = { left: 84, right: 30, top: 34, bottom: 70 };
    var xDomain = scaleDomain(points.map(function (point) {
      return point.kapasitas_l;
    }), false);
    var yDomain = scaleDomain(points.map(function (point) {
      return point.harga_rp;
    }), true);
    var plotWidth = width - pad.left - pad.right;
    var plotHeight = height - pad.top - pad.bottom;
    var x = function (value) {
      return pad.left + (value - xDomain.min) / (xDomain.max - xDomain.min) * plotWidth;
    };
    var y = function (value) {
      return pad.top + (1 - (value - yDomain.min) / (yDomain.max - yDomain.min)) * plotHeight;
    };
    var brands = unique(points.map(function (point) { return point.brand; }));
    var colors = colorMap(brands);
    renderLegend(brands, colors);

    var svg = svgEl("svg", {
      viewBox: "0 0 " + width + " " + height,
      role: "img",
      "aria-labelledby": "benchmarkScatterSvgTitle benchmarkScatterSvgDesc"
    });
    var title = svgEl("title", { id: "benchmarkScatterSvgTitle" });
    title.textContent = "Scatter kapasitas versus harga kulkas";
    svg.appendChild(title);
    var description = svgEl("desc", { id: "benchmarkScatterSvgDesc" });
    description.textContent = "Setiap titik adalah model yang memiliki kapasitas dan harga pada sumber benchmark.";
    svg.appendChild(description);

    for (var xTick = xDomain.min; xTick <= xDomain.max + xDomain.step / 2; xTick += xDomain.step) {
      svg.appendChild(svgEl("line", {
        x1: x(xTick), y1: pad.top, x2: x(xTick), y2: height - pad.bottom,
        stroke: "currentColor", "stroke-opacity": "0.12"
      }));
      svg.appendChild(svgText(number.format(xTick) + " L", {
        x: x(xTick), y: height - pad.bottom + 24, "text-anchor": "middle",
        "font-size": "12", fill: "currentColor", opacity: "0.7"
      }));
    }
    for (var yTick = yDomain.min; yTick <= yDomain.max + yDomain.step / 2; yTick += yDomain.step) {
      svg.appendChild(svgEl("line", {
        x1: pad.left, y1: y(yTick), x2: width - pad.right, y2: y(yTick),
        stroke: "currentColor", "stroke-opacity": "0.12"
      }));
      svg.appendChild(svgText(formatAxisPrice(yTick), {
        x: pad.left - 12, y: y(yTick) + 4, "text-anchor": "end",
        "font-size": "12", fill: "currentColor", opacity: "0.7"
      }));
    }

    svg.appendChild(svgText("Kapasitas (L)", {
      x: pad.left + plotWidth / 2, y: height - 16, "text-anchor": "middle",
      "font-size": "13", "font-weight": "700", fill: "currentColor", opacity: "0.78"
    }));
    svg.appendChild(svgText("Harga (Rp)", {
      x: 20, y: pad.top + plotHeight / 2, "text-anchor": "middle",
      "font-size": "13", "font-weight": "700", fill: "currentColor", opacity: "0.78",
      transform: "rotate(-90 20 " + (pad.top + plotHeight / 2) + ")"
    }));

    points.forEach(function (point) {
      var circle = svgEl("circle", {
        cx: x(point.kapasitas_l),
        cy: y(point.harga_rp),
        r: "5.5",
        fill: colors[point.brand],
        stroke: "#ffffff",
        "stroke-width": "1.5",
        opacity: point.brand === "AQUA" ? "0.96" : "0.78",
        tabindex: "0",
        "aria-label": point.brand + " " + point.model + ", " +
          number.format(point.kapasitas_l) + " liter, " + currency.format(point.harga_rp)
      });
      var tooltip = svgEl("title", {});
      tooltip.textContent = point.brand + " · " + point.model + " · " +
        number.format(point.kapasitas_l) + " L · " + currency.format(point.harga_rp);
      circle.appendChild(tooltip);
      svg.appendChild(circle);
    });
    host.replaceChildren(svg);
  }

  function render() {
    var records = filteredModels();
    renderScatter(records);
    renderTable(records);
  }

  function setSummary(payload) {
    var aquaCount = state.models.filter(function (record) {
      return record.brand === "AQUA";
    }).length;
    var competitorCount = unique(state.models.filter(function (record) {
      return record.brand !== "AQUA";
    }).map(function (record) {
      return record.brand;
    })).length;
    var pricedCount = state.models.filter(function (record) {
      return record.harga_rp !== null;
    }).length;
    byId("benchmarkSummary").textContent = number.format(state.models.length) +
      " model · " + number.format(aquaCount) + " AQUA · " +
      number.format(competitorCount) + " brand kompetitor · " +
      number.format(pricedCount) + " punya harga";

    var generated = payload.meta && payload.meta.digenerate;
    var generatedNode = byId("generatedAt");
    if (typeof generated === "string") {
      var parsed = new Date(generated);
      generatedNode.dateTime = generated;
      generatedNode.textContent = isNaN(parsed.getTime()) ? generated :
        new Intl.DateTimeFormat("id-ID", {
          dateStyle: "medium",
          timeStyle: "short",
          timeZone: "Asia/Jakarta"
        }).format(parsed) + " WIB";
    }
  }

  function bindControls() {
    byId("brandFilter").addEventListener("change", function (event) {
      state.brand = event.target.value;
      render();
    });
    byId("typeFilter").addEventListener("change", function (event) {
      state.type = event.target.value;
      render();
    });
    document.querySelectorAll(".sort-button[data-sort]").forEach(function (button) {
      button.addEventListener("click", function () {
        var key = button.dataset.sort;
        if (state.sortKey === key) {
          state.sortDirection *= -1;
        } else {
          state.sortKey = key;
          state.sortDirection = 1;
        }
        renderTable(filteredModels());
      });
    });
  }

  function showError(message) {
    var error = byId("loadError");
    error.hidden = false;
    error.textContent = message;
    byId("benchmarkSummary").textContent = "Data benchmark gagal dimuat.";
  }

  fetch(DATA_URL, { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    })
    .then(function (payload) {
      if (!payload || !Array.isArray(payload.models)) {
        throw new Error("struktur JSON tidak valid");
      }
      state.models = payload.models.filter(isModel);
      state.sourceFiles = payload.meta && Array.isArray(payload.meta.sumber_files) ?
        payload.meta.sumber_files.slice() :
        unique(state.models.map(function (record) { return record.sumber_file; }));
      populateFilter(byId("brandFilter"), unique(state.models.map(function (record) {
        return record.brand;
      })));
      populateFilter(byId("typeFilter"), unique(state.models.map(function (record) {
        return record.tipe_pintu;
      })));
      setSummary(payload);
      bindControls();
      render();
    })
    .catch(function (error) {
      showError("Tidak bisa memuat " + DATA_URL + ": " + error.message);
    });
}());
