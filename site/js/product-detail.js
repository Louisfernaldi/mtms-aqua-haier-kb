(function (window, document) {
  "use strict";

  if (window.MTMSProductDetail && typeof window.MTMSProductDetail.open === "function") return;

  var MISSING = "Belum tersedia";
  var FAILED_IMAGE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480"><rect width="640" height="480" fill="#f4f8fb"/><g fill="none" stroke="#718096" stroke-width="12"><rect x="220" y="112" width="200" height="164" rx="16"/><path d="m240 252 58-62 48 48 30-32 44 46"/><circle cx="368" cy="158" r="18"/></g><text x="320" y="350" fill="#52606d" font-family="Arial,sans-serif" font-size="28" text-anchor="middle">Foto gagal dimuat</text></svg>';
  var FAILED_IMAGE_SRC = "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(FAILED_IMAGE_SVG);
  var modal = null;
  var bodyLockState = null;
  var previousFocus = null;
  var sectionNavigationCleanup = null;
  var researchConfig = { wired: false, liveReady: null, getWriteSha: null, onChanged: null };
  var researchPollTimer = 0;
  var RESEARCH_MAX_POLLS = 12;
  var CORE_CATEGORIES = [
    { key: "form_factor", label: "Tipe Kulkas", group: "Konfigurasi", unit: "-", comparison: true, order: 10, active: true },
    { key: "door_count", label: "Jumlah Pintu", group: "Konfigurasi", unit: "pintu", comparison: true, order: 20, active: true },
    { key: "freezer_position", label: "Posisi Freezer", group: "Konfigurasi", unit: "-", comparison: true, order: 30, active: true },
    { key: "gross_capacity_l", label: "Kapasitas Kotor", group: "Kapasitas", unit: "L", comparison: true, order: 40, active: true },
    { key: "net_capacity_l", label: "Kapasitas Bersih", group: "Kapasitas", unit: "L", comparison: true, order: 50, active: true },
    { key: "width_mm", label: "Lebar", group: "Dimensi", unit: "mm", comparison: true, order: 60, active: true },
    { key: "height_mm", label: "Tinggi", group: "Dimensi", unit: "mm", comparison: true, order: 70, active: true },
    { key: "depth_mm", label: "Kedalaman", group: "Dimensi", unit: "mm", comparison: true, order: 80, active: true },
    { key: "rated_power_w", label: "Daya Listrik", group: "Performa", unit: "W", comparison: true, order: 90, active: true },
    { key: "compressor_type", label: "Jenis Kompresor", group: "Performa", unit: "-", comparison: true, order: 100, active: true },
    { key: "cooling_system", label: "Sistem Pendinginan", group: "Performa", unit: "-", comparison: true, order: 110, active: true },
    { key: "defrost_type", label: "Sistem Defrost", group: "Performa", unit: "-", comparison: true, order: 120, active: true }
  ];
  var categoryState = {
    categories: cloneCategories(CORE_CATEGORIES),
    source: "fallback",
    sha: "",
    listeners: []
  };

  function cloneCategories(categories) {
    return categories.map(function (category) {
      return {
        key: category.key,
        label: category.label,
        group: category.group,
        unit: category.unit,
        comparison: category.comparison === true,
        order: category.order,
        active: category.active === true
      };
    });
  }

  function categoryItems(payload) {
    if (Array.isArray(payload)) return payload;
    return payload && Array.isArray(payload.spec_categories) ? payload.spec_categories : [];
  }

  function validatedCategories(payload) {
    var items = categoryItems(payload);
    var seenKeys = Object.create(null);
    var seenOrders = Object.create(null);
    var result = [];
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      if (!item || typeof item !== "object" || Array.isArray(item)) return null;
      var key = typeof item.key === "string" ? item.key.trim() : "";
      var label = typeof item.label === "string" ? item.label.trim() : "";
      var group = typeof item.group === "string" ? item.group.trim() : "";
      var unit = typeof item.unit === "string" ? item.unit.trim() : "";
      var order = Number(item.order);
      if (!key || !label || !group || !unit || !Number.isFinite(order) ||
          typeof item.active !== "boolean" || typeof item.comparison !== "boolean" ||
          seenKeys[key] || seenOrders[String(order)]) return null;
      seenKeys[key] = true;
      seenOrders[String(order)] = true;
      result.push({
        key: key,
        label: label,
        group: group,
        unit: unit,
        comparison: item.comparison,
        order: order,
        active: item.active
      });
    }
    for (var coreIndex = 0; coreIndex < CORE_CATEGORIES.length; coreIndex++) {
      if (!seenKeys[CORE_CATEGORIES[coreIndex].key]) return null;
    }
    return result.sort(function (a, b) { return a.order - b.order || a.key.localeCompare(b.key); });
  }

  function publishCategories(payload, source, sha) {
    var categories = validatedCategories(payload);
    if (!categories) return false;
    categoryState.categories = categories;
    categoryState.source = source;
    categoryState.sha = sha || "";
    categoryState.listeners.slice().forEach(function (listener) {
      try { listener(cloneCategories(categories), source); } catch (_error) { /* subscriber owns its UI */ }
    });
    return true;
  }

  function scalarValue(value) {
    if (typeof value === "boolean") return value ? "Ya" : "Tidak";
    if (typeof value === "string" || typeof value === "number") return hasValue(value) ? String(value) : "";
    return "";
  }

  function unitAlreadyPresent(text, unit) {
    var escaped = String(unit).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp("(^|[\\s(,/])" + escaped + "(?=$|[\\s),/])", "i").test(text);
  }

  function formatSpecEntry(entry, category) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry) || !hasValue(entry.value)) return MISSING;
    var text;
    if (Array.isArray(entry.value)) {
      var parts = entry.value.map(scalarValue).filter(function (part) { return part !== ""; });
      text = parts.join(", ");
    } else {
      text = scalarValue(entry.value);
    }
    if (!text) return MISSING;
    var unit = category && hasValue(category.unit) && category.unit !== "-" ? String(category.unit).trim() : "";
    return unit && !unitAlreadyPresent(text, unit) ? text + " " + unit : text;
  }

  window.MTMSSpecCategories = {
    staticUrl: "data/spec-categories.json",
    liveUrl: "api/spec-categories",
    get: function () { return cloneCategories(categoryState.categories); },
    getState: function () {
      return { source: categoryState.source, sha: categoryState.sha, categories: cloneCategories(categoryState.categories) };
    },
    subscribe: function (listener) {
      if (typeof listener !== "function") return function () {};
      categoryState.listeners.push(listener);
      return function () {
        categoryState.listeners = categoryState.listeners.filter(function (item) { return item !== listener; });
      };
    },
    formatValue: formatSpecEntry,
    missingLabel: MISSING
  };

  function startCategoryLoad() {
    if (typeof window.fetch !== "function") return;
    window.fetch("data/spec-categories.json", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("static categories " + response.status);
        return response.json();
      })
      .then(function (payload) { publishCategories(payload, "static", ""); })
      .catch(function () { /* the 12-core fallback is already usable */ })
      .then(function () {
        if (window.location.protocol !== "http:" && window.location.protocol !== "https:") return null;
        return window.fetch("api/spec-categories", { credentials: "same-origin" })
          .then(function (response) {
            if (!response.ok) throw new Error("api categories " + response.status);
            var sha = String(response.headers.get("X-Data-SHA") || response.headers.get("ETag") || "")
              .replace(/^W\//, "").replace(/^\"|\"$/g, "");
            return response.json().then(function (payload) { publishCategories(payload, "api", sha); });
          });
      })
      .catch(function () { /* static/fallback categories remain authoritative for this view */ });
  }

  startCategoryLoad();

  function inlineStyleState(style, property) {
    return {
      value: style.getPropertyValue(property),
      priority: style.getPropertyPriority(property)
    };
  }

  function lockBody() {
    if (bodyLockState !== null) return;
    var body = document.body;
    var style = body.style;
    bodyLockState = {
      scrollY: window.scrollY,
      hadStyleAttribute: body.hasAttribute("style"),
      position: inlineStyleState(style, "position"),
      top: inlineStyleState(style, "top"),
      width: inlineStyleState(style, "width"),
      overflow: inlineStyleState(style, "overflow")
    };
    style.setProperty("position", "fixed");
    style.setProperty("top", -bodyLockState.scrollY + "px");
    style.setProperty("width", "100%");
    style.setProperty("overflow", "hidden");
  }

  function restoreInlineStyle(style, property, state) {
    if (state.value) {
      style.setProperty(property, state.value, state.priority);
    } else {
      style.removeProperty(property);
    }
  }

  function unlockBody() {
    if (bodyLockState === null) return;
    var state = bodyLockState;
    var body = document.body;
    var style = body.style;
    bodyLockState = null;
    restoreInlineStyle(style, "position", state.position);
    restoreInlineStyle(style, "top", state.top);
    restoreInlineStyle(style, "width", state.width);
    restoreInlineStyle(style, "overflow", state.overflow);
    if (!state.hadStyleAttribute && body.getAttribute("style") === "") {
      body.removeAttribute("style");
    }
    window.scrollTo(0, state.scrollY);
  }

  function hasValue(value) {
    if (value === null || value === undefined) return false;
    if (typeof value === "string") return value.trim() !== "";
    if (Array.isArray(value)) return value.some(hasValue);
    return true;
  }

  function display(value) {
    return hasValue(value) ? String(value) : MISSING;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/`/g, "&#96;");
  }

  function safeLink(value) {
    if (!hasValue(value)) return "";
    var url = String(value).trim();
    if (!url || /[\u0000-\u001f\u007f\\]/.test(url) || /^\/\//.test(url)) return "";
    var explicitHttp = /^https?:\/\//i.test(url);
    var explicitScheme = /^[a-z][a-z0-9+.-]*:/i.test(url);
    if (explicitScheme && !explicitHttp) return "";
    try {
      var parsed = new URL(url, window.location.href);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return "";
      if (!explicitHttp && parsed.origin !== window.location.origin) return "";
      return url;
    } catch (_error) {
      return "";
    }
  }

  function safeImage(value) {
    if (!hasValue(value)) return "";
    var url = String(value).trim();
    if (/^data:image\/(?:png|jpe?g|gif|webp);base64,/i.test(url)) return url;
    var safe = safeLink(url);
    if (!safe) return "";
    try {
      var parsed = new URL(safe, window.location.href);
      if (parsed.origin === window.location.origin || parsed.protocol === "https:") return safe;
    } catch (_error) { return ""; }
    return "";
  }

  function showImageFallback(image) {
    if (!image || image.getAttribute("data-image-fallback") === "true") return;
    image.setAttribute("data-image-fallback", "true");
    image.alt = "Foto gagal dimuat";
    image.removeAttribute("srcset");
    image.src = FAILED_IMAGE_SRC;
  }

  function wireImageFallback(image) {
    if (!image || image.getAttribute("data-image-fallback-wired") === "true") return;
    image.setAttribute("data-image-fallback-wired", "true");
    image.setAttribute("data-original-alt", image.alt || "");
    image.addEventListener("error", function () { showImageFallback(image); });
    if (image.complete && image.naturalWidth === 0) showImageFallback(image);
  }

  function setImageSource(image, source) {
    image.removeAttribute("data-image-fallback");
    image.alt = image.getAttribute("data-original-alt") || "";
    image.src = source;
  }

  function wirePhotoFallbacks(scope) {
    scope.querySelectorAll("img.pk-gal-img, .pk-gal-thumb img").forEach(wireImageFallback);
  }

  function formatRupiah(value) {
    if (!hasValue(value)) return MISSING;
    var digits = String(value).replace(/\./g, "").replace(/\D/g, "");
    if (!digits) return MISSING;
    return "Rp " + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function withUnit(value, unit) {
    if (!hasValue(value)) return MISSING;
    var text = String(value);
    return new RegExp("\\b" + unit + "\\b", "i").test(text) ? text : text + " " + unit;
  }

  function listValue(value) {
    if (!Array.isArray(value)) return hasValue(value) ? String(value) : "";
    var values = value.filter(hasValue).map(String);
    return values.length ? values.join(", ") : "";
  }

  function capacityValue(record) {
    var parts = [];
    if (hasValue(record.kapasitas_gross)) parts.push(record.kapasitas_gross + " L gross");
    if (hasValue(record.kapasitas_nett)) parts.push(record.kapasitas_nett + " L nett");
    return parts.join(" / ");
  }

  function rowHtml(label, value, note) {
    var html = "<tr><th>" + escapeHtml(label) + "</th><td>" + escapeHtml(value);
    if (hasValue(note)) html += '<span class="pk-detail-note">' + escapeHtml(note) + "</span>";
    return html + "</td></tr>";
  }

  function specRowsHtml(specs) {
    var rows = [];
    var missing = [];
    specs.forEach(function (spec) {
      if (hasValue(spec.value)) {
        rows.push(rowHtml(spec.label, spec.value, spec.note));
      } else {
        missing.push(spec.label);
      }
    });
    if (missing.length) {
      rows.push('<tr class="pk-detail-missing"><th>' + MISSING + "</th><td>" +
        escapeHtml(missing.join(", ")) + "</td></tr>");
    }
    return rows.join("");
  }

  function formatPriceSource(value) {
    if (!hasValue(value)) return "";
    return String(value)
      .replace(/_/g, " ")
      .replace(/\bgfk\b/gi, "GfK")
      .replace(/\(brief\)/gi, "(ringkasan riset)");
  }

  function humanSourceKind(value) {
    var key = String(value || "").trim().toLowerCase();
    var labels = {
      official_product_page: "Halaman produk resmi",
      official_catalog: "Katalog resmi",
      official_document: "Dokumen resmi",
      marketplace_product_page: "Halaman produk marketplace",
      retailer_product_page: "Halaman produk toko",
      market_research: "Riset pasar",
      research: "Hasil riset",
      user_input: "Masukan pengguna",
      legacy_import: "Data lama",
      unknown: "Belum diketahui"
    };
    return labels[key] || "Sumber lainnya";
  }

  function humanOrigin(value) {
    var key = String(value || "unknown").trim().toLowerCase();
    var labels = {
      research: "Hasil riset",
      user: "Masukan pengguna",
      legacy: "Data lama",
      unknown: "Belum diketahui"
    };
    return labels[key] || "Sumber lainnya";
  }

  function formatVerifiedAt(value) {
    var date = new Date(String(value || ""));
    if (Number.isNaN(date.getTime())) return "Waktu belum dapat dibaca";
    try {
      return new Intl.DateTimeFormat("id-ID", {
        timeZone: "Asia/Jakarta",
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23"
      }).format(date).replace(/\./g, ":") + " WIB";
    } catch (_error) {
      return "Waktu tercatat (WIB)";
    }
  }

  function photoList(record) {
    var values = [];
    if (Array.isArray(record.foto_list)) values = values.concat(record.foto_list);
    values.push(record.foto, record.image, record.photo);
    var seen = {};
    return values.map(safeImage).filter(function (url) {
      if (!url || seen[url]) return false;
      seen[url] = true;
      return true;
    });
  }

  function missingPhotoHtml(record) {
    var svg = '<svg class="pk-noimg-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 7h10"/><path d="M7 11h6"/><path d="M7 15h4"/><line x1="12" y1="19" x2="12" y2="21"/></svg>';
    var hasReference = hasValue(record.foto) || hasValue(record.image) || hasValue(record.photo) ||
      (Array.isArray(record.foto_list) && record.foto_list.some(hasValue));
    return '<div class="pk-thumb pk-noimg pk-detail-missing-photo">' + svg +
      '<span class="pk-noimg-label">' + (hasReference ? "Foto tersedia di sumber" : MISSING) + "</span></div>";
  }

  function photosHtml(record, photos) {
    var alt = escapeAttr(display(record.model));
    if (!photos.length) return missingPhotoHtml(record);
    if (photos.length === 1) {
      return '<img class="pk-modal-img pk-gal-img" src="' + escapeAttr(photos[0]) +
        '" alt="' + alt + '">';
    }
    var thumbs = photos.map(function (photo, index) {
      return '<button type="button" class="pk-gal-thumb' + (index === 0 ? " active" : "") +
        '" data-idx="' + index + '" aria-label="Foto ' + (index + 1) + '">' +
        '<img src="' + escapeAttr(photo) + '" alt=""></button>';
    }).join("");
    return '<div class="pk-gal"><div class="pk-gal-stage">' +
      '<button type="button" class="pk-gal-nav" data-dir="-1" aria-label="Foto sebelumnya">&#8249;</button>' +
      '<img class="pk-modal-img pk-gal-img" src="' + escapeAttr(photos[0]) +
      '" alt="' + alt + '" data-idx="0">' +
      '<button type="button" class="pk-gal-nav" data-dir="1" aria-label="Foto berikutnya">&#8250;</button>' +
      '</div><div class="pk-gal-thumbs">' + thumbs + "</div></div>";
  }

  function flagsHtml(record) {
    if (!Array.isArray(record.flags) || !record.flags.length) return "";
    return record.flags.filter(hasValue).map(function (flag) {
      var css = String(flag).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      return '<span class="badge ' + escapeAttr(css) + '">' + escapeHtml(flag) + "</span>";
    }).join("");
  }

  function featuresHtml(record) {
    var features = featureValues(record);
    if (!features.length) return '<p class="pk-benefit pk-detail-missing">' + MISSING + "</p>";
    return '<ul class="pk-fitur">' + features.map(function (feature) {
      return "<li>" + escapeHtml(feature) + "</li>";
    }).join("") + "</ul>";
  }

  function featureValues(record) {
    var features = Array.isArray(record.fitur) ? record.fitur.filter(hasValue) : [];
    if (!features.length && Array.isArray(record.features)) features = record.features.filter(hasValue);
    return features;
  }

  function provenanceHtml(meta, className, includeLock) {
    meta = meta && typeof meta === "object" && !Array.isArray(meta) ? meta : {};
    var sourceUrl = safeLink(meta.source_url);
    var parts = [];
    if (sourceUrl) {
      parts.push('<div class="pk-provenance-row pk-provenance-link" data-provenance-field="source-link">' +
        '<span class="pk-provenance-label">Sumber:</span> <a href="' + escapeAttr(sourceUrl) +
        '" target="_blank" rel="noopener noreferrer">Buka sumber nilai</a></div>');
    }
    if (hasValue(meta.source_kind)) {
      parts.push('<div class="pk-provenance-row" data-provenance-field="source-kind" data-source-kind="' +
        escapeAttr(meta.source_kind) + '"><span class="pk-provenance-label">Jenis sumber:</span> ' +
        '<span class="pk-provenance-chip">' + escapeHtml(humanSourceKind(meta.source_kind)) + "</span></div>");
    }
    if (hasValue(meta.verified_at)) {
      parts.push('<div class="pk-provenance-row" data-provenance-field="verified-at"><span class="pk-provenance-label">Diverifikasi:</span> ' +
        '<time class="pk-provenance-chip" datetime="' + escapeAttr(meta.verified_at) + '">' +
        escapeHtml(formatVerifiedAt(meta.verified_at)) + "</time></div>");
    }
    var rawOrigin = hasValue(meta.origin) ? meta.origin : "unknown";
    parts.push('<div class="pk-provenance-row" data-provenance-field="origin" data-origin="' +
      escapeAttr(rawOrigin) + '"><span class="pk-provenance-label">Asal data:</span> ' +
      '<span class="pk-provenance-chip">' + escapeHtml(humanOrigin(rawOrigin)) + "</span></div>");
    if (includeLock) {
      parts.push('<div class="pk-provenance-row" data-provenance-field="user-protection" data-user-protection="' +
        (meta.user_locked === true ? "protected" : "updatable") +
        '"><span class="pk-provenance-label">Perlindungan nilai:</span> <span class="pk-provenance-chip">' +
        (meta.user_locked === true ? "tidak dapat ditimpa otomatis" : "dapat diperbarui dari riset") + "</span></div>");
    }
    return '<div class="pk-provenance ' + escapeAttr(className) + '" data-provenance-group="true">' +
      parts.join("") + "</div>";
  }

  function orderedCategories(options) {
    var supplied = options && options.categories;
    var categories = validatedCategories(supplied) || cloneCategories(categoryState.categories);
    return categories.sort(function (a, b) { return a.order - b.order || a.key.localeCompare(b.key); });
  }

  function activeCategories(options) {
    return orderedCategories(options).filter(function (category) { return category.active === true; });
  }

  function dynamicSpecsHtml(record, options) {
    var categories = activeCategories(options);
    var groups = [];
    var byGroup = Object.create(null);
    categories.forEach(function (category) {
      if (!byGroup[category.group]) {
        byGroup[category.group] = [];
        groups.push(category.group);
      }
      byGroup[category.group].push(category);
    });
    var values = record.spec_values && typeof record.spec_values === "object" && !Array.isArray(record.spec_values) ? record.spec_values : {};
    return '<div class="pk-dynamic-specs">' + groups.map(function (group) {
      var missing = [];
      var missingKeys = [];
      var rows = [];
      byGroup[group].forEach(function (category) {
        var entry = values[category.key];
        if (!entry || !hasValue(entry.value)) {
          missing.push(category.label);
          missingKeys.push(category.key);
          return;
        }
        rows.push('<div class="pk-spec-row" data-spec-key="' + escapeAttr(category.key) + '">' +
          '<dt>' + escapeHtml(category.label) + '</dt><dd><span class="pk-spec-value">' +
          escapeHtml(formatSpecEntry(entry, category)) + "</span>" +
          provenanceHtml(entry, "pk-spec-provenance", true) + "</dd></div>");
      });
      var missingHtml = missing.length ? '<div class="pk-spec-missing" data-missing-keys="' + escapeAttr(missingKeys.join(",")) + '"><strong>' + MISSING +
        ":</strong> " + escapeHtml(missing.join(", ")) + "</div>" : "";
      return '<section class="pk-spec-group" data-spec-group="' + escapeAttr(group) + '"><h5>' +
        escapeHtml(group) + "</h5><dl>" + rows.join("") + "</dl>" + missingHtml + "</section>";
    }).join("") + "</div>";
  }

  function suggestionsHtml(record, options) {
    var suggestions = Array.isArray(record.research_suggestions) ? record.research_suggestions : [];
    if (!suggestions.length) return "";
    var categoryMap = Object.create(null);
    orderedCategories(options).forEach(function (category) { categoryMap[category.key] = category; });
    var statusLabels = { pending: "Pending", accepted: "Diterima", rejected: "Ditolak" };
    var statusClasses = {
      pending: "pk-suggestion-pending",
      accepted: "pk-suggestion-accepted",
      rejected: "pk-suggestion-rejected"
    };
    return '<h4 id="mtms-product-detail-saran">Saran riset</h4><div class="pk-research-suggestions">' + suggestions.map(function (suggestion) {
      suggestion = suggestion && typeof suggestion === "object" && !Array.isArray(suggestion) ? suggestion : {};
      var category = categoryMap[suggestion.key] || { key: suggestion.key || "unknown", label: suggestion.key || "Kategori tidak dikenal", unit: "-" };
      var status = Object.prototype.hasOwnProperty.call(statusLabels, suggestion.status) ? suggestion.status : "pending";
      return '<article class="pk-suggestion ' + statusClasses[status] + ' is-' + status + '" data-suggestion-status="' + status + '">' +
        '<div class="pk-suggestion-head"><strong>' + escapeHtml(category.label) + '</strong><span class="pk-suggestion-status">' +
        statusLabels[status] + "</span></div>" +
        '<p class="pk-suggestion-value"><span>Usulan:</span> ' + escapeHtml(formatSpecEntry({ value: suggestion.value }, category)) + "</p>" +
        provenanceHtml(suggestion, "pk-suggestion-provenance", false) + "</article>";
    }).join("") + "</div>";
  }

  function configureResearch(options) {
    options = options || {};
    if (typeof options.liveReady === "function") researchConfig.liveReady = options.liveReady;
    if (typeof options.getWriteSha === "function") researchConfig.getWriteSha = options.getWriteSha;
    if (typeof options.onChanged === "function") researchConfig.onChanged = options.onChanged;
    researchConfig.wired = Boolean(researchConfig.liveReady && researchConfig.getWriteSha && researchConfig.onChanged);
  }

  function clearResearchPoll() {
    if (researchPollTimer) window.clearTimeout(researchPollTimer);
    researchPollTimer = 0;
  }

  function researchModelId(record) {
    var model = record && typeof record.model === "string" ? record.model.trim() : "";
    if (!model) return "";
    return (record.brand && String(record.brand).trim() || "AQUA") + "::" + model;
  }

  function researchRequest(method, body, extraHeaders) {
    return window.fetch("api/research", {
      method: method,
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, extraHeaders || {}),
      body: body === undefined ? undefined : JSON.stringify(body)
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (payload) {
        return { status: response.status, ok: response.ok, payload: payload };
      });
    });
  }

  function getResearchJob(jobId) {
    return window.fetch("api/research?job_id=" + encodeURIComponent(jobId), { credentials: "same-origin" })
      .then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (payload) {
          return { status: response.status, ok: response.ok, payload: payload };
        });
      });
  }

  function setResearchStatus(box, message, kind) {
    var status = box.querySelector(".pk-research-status");
    if (!status) return;
    status.textContent = message || "";
    status.className = "pk-research-status" + (kind ? " is-" + kind : "");
  }

  function researchCategoryMap(options) {
    var map = Object.create(null);
    orderedCategories(options).forEach(function (category) { map[category.key] = category; });
    return map;
  }

  function candidateCardHtml(candidate, category, jobId) {
    return '<article class="pk-research-candidate is-pending" data-suggestion-id="' +
      escapeAttr(candidate.suggestion_id) + '" data-job-id="' + escapeAttr(jobId) + '">' +
      '<div class="pk-research-head"><strong>' + escapeHtml(category ? category.label : candidate.key) + "</strong></div>" +
      '<p class="pk-research-value"><span>Usulan:</span> ' +
      escapeHtml(formatSpecEntry({ value: candidate.value }, category)) + "</p>" +
      provenanceHtml(candidate, "pk-research-provenance", false) +
      '<div class="pk-research-actions">' +
      '<button type="button" class="pk-research-accept">Terima</button>' +
      '<button type="button" class="pk-research-reject">Tolak</button>' +
      "</div></article>";
  }

  function renderResearchOutcome(box, job, categoryMap) {
    var host = box.querySelector(".pk-research-candidates");
    if (!host) return;
    var candidates = Array.isArray(job.candidates) ? job.candidates.filter(function (item) {
      return item && item.status === "pending";
    }) : [];
    if (job.status === "completed" && candidates.length) {
      host.innerHTML = candidates.map(function (candidate) {
        return candidateCardHtml(candidate, categoryMap[candidate.key], job.job_id);
      }).join("");
      setResearchStatus(box, "Riset selesai. Periksa usulan di bawah.", "ok");
      wireCandidateActions(box);
      return;
    }
    host.innerHTML = "";
    if (job.status === "completed") setResearchStatus(box, "Riset selesai tanpa usulan baru.", "info");
    else if (job.status === "unresolved") setResearchStatus(box, "Sumber tidak mengonfirmasi model ini.", "info");
    else if (job.status === "failed") setResearchStatus(box, "Riset gagal dijalankan. Coba lagi nanti.", "error");
    else setResearchStatus(box, "Riset masih berjalan...", "info");
  }

  function markDecision(card, kind, message) {
    card.classList.remove("is-pending");
    card.classList.add(kind === "accept" ? "is-accepted" : "is-rejected");
    var actions = card.querySelector(".pk-research-actions");
    if (actions) actions.remove();
    var box = card.closest(".pk-research");
    if (box && message) setResearchStatus(box, message, kind === "accept" ? "ok" : "info");
  }

  function handleDecision(card, action) {
    var box = card.closest(".pk-research");
    if (!box) return;
    var jobId = card.getAttribute("data-job-id");
    var suggestionId = card.getAttribute("data-suggestion-id");
    var buttons = card.querySelectorAll(".pk-research-actions button");
    buttons.forEach(function (button) { button.disabled = true; });
    var headers = null;
    if (action === "accept") {
      var sha = typeof researchConfig.getWriteSha === "function" ? researchConfig.getWriteSha() : "";
      if (!sha) {
        setResearchStatus(box, "Muat ulang halaman dulu supaya SHA terbaru.", "error");
        buttons.forEach(function (button) { button.disabled = false; });
        return;
      }
      headers = { "If-Match": '"' + sha + '"' };
    }
    researchRequest("PATCH", { action: action, job_id: jobId, suggestion_id: suggestionId }, headers)
      .then(function (result) {
        if (result.ok) {
          markDecision(card, action, action === "accept" ?
            "Nilai diterima dan dikunci sebagai editan tim." :
            "Usulan ditolak.");
          if (action === "accept" && typeof researchConfig.onChanged === "function") {
            researchConfig.onChanged();
          }
          return;
        }
        buttons.forEach(function (button) { button.disabled = false; });
        if (result.status === 412 || result.status === 409) {
          setResearchStatus(box, "Nilai sudah berubah sebelum diproses. Muat ulang halaman lalu ulangi.", "error");
          if (typeof researchConfig.onChanged === "function") researchConfig.onChanged();
        } else if (result.status === 401) {
          setResearchStatus(box, "Login dulu untuk memproses usulan.", "error");
        } else if (result.status === 403) {
          setResearchStatus(box, "Akses ditolak.", "error");
        } else if (result.status === 404) {
          setResearchStatus(box, "Usulan tidak ditemukan; daftar mungkin sudah diperbarui.", "error");
        } else {
          setResearchStatus(box, "Proses gagal. Coba lagi.", "error");
        }
      })
      .catch(function () {
        buttons.forEach(function (button) { button.disabled = false; });
        setResearchStatus(box, "Jaringan bermasalah. Coba lagi.", "error");
      });
  }

  function wireCandidateActions(box) {
    box.querySelectorAll(".pk-research-candidate").forEach(function (card) {
      var accept = card.querySelector(".pk-research-accept");
      var reject = card.querySelector(".pk-research-reject");
      if (accept) accept.addEventListener("click", function () { handleDecision(card, "accept"); });
      if (reject) reject.addEventListener("click", function () { handleDecision(card, "reject"); });
    });
  }

  function pollResearchJob(box, jobId, delay, pollsLeft, categoryMap) {
    clearResearchPoll();
    if (pollsLeft <= 0) {
      setResearchStatus(box, "Riset masih berjalan di latar. Buka ulang modal nanti untuk hasil.", "info");
      return;
    }
    researchPollTimer = window.setTimeout(function () {
      getResearchJob(jobId).then(function (result) {
        if (!modal || !modal.classList.contains("open")) return;
        if (!result.ok) {
          setResearchStatus(box, result.status === 401 ?
            "Login dulu untuk melihat status riset." :
            "Status riset gagal dimuat.", "error");
          return;
        }
        var job = result.payload || {};
        if (job.status === "queued" || job.status === "running") {
          setResearchStatus(box, "Riset masih berjalan...", "info");
          pollResearchJob(box, jobId, delay, pollsLeft - 1, categoryMap);
          return;
        }
        renderResearchOutcome(box, job, categoryMap);
      }).catch(function () {
        setResearchStatus(box, "Jaringan bermasalah saat mengecek riset.", "error");
      });
    }, delay);
  }

  function startResearch(button, box, categoryMap) {
    var modelId = box.getAttribute("data-model-id") || "";
    button.disabled = true;
    setResearchStatus(box, "Mendaftarkan riset...", "info");
    researchRequest("POST", { model_id: modelId }).then(function (result) {
      if (result.status === 202 && result.payload && result.payload.job_id) {
        setResearchStatus(box, "Riset antre. Sedang dicek berkala...", "info");
        var delay = Number(result.payload.poll_after_ms);
        pollResearchJob(box, result.payload.job_id,
          Number.isFinite(delay) && delay >= 200 ? Math.min(delay, 5000) : 2000,
          RESEARCH_MAX_POLLS, categoryMap);
        return;
      }
      button.disabled = false;
      if (result.status === 401) setResearchStatus(box, "Login dulu untuk memakai riset.", "error");
      else if (result.status === 403) setResearchStatus(box, "Akses ditolak.", "error");
      else if (result.status === 404) setResearchStatus(box, "Model tidak ada di data live.", "error");
      else if (result.status === 503) setResearchStatus(box, "Riset sedang sibuk. Coba lagi nanti.", "error");
      else setResearchStatus(box, "Riset gagal dijalankan.", "error");
    }).catch(function () {
      button.disabled = false;
      setResearchStatus(box, "Jaringan bermasalah. Coba lagi.", "error");
    });
  }

  function wireResearch(record, options) {
    clearResearchPoll();
    var box = modal.querySelector('.pk-research[data-model-id]');
    if (!box) return;
    var start = box.querySelector(".pk-research-start");
    if (!start) return;
    var ready = typeof researchConfig.liveReady === "function" ? researchConfig.liveReady() : true;
    start.disabled = !ready;
    if (!ready) setResearchStatus(box, "Menunggu data live sebelum riset bisa dijalankan.", "info");
    start.addEventListener("click", function () {
      startResearch(start, box, researchCategoryMap(options));
    });
  }

  function researchSectionHtml(record) {
    if (!researchConfig.wired) return "";
    var modelId = researchModelId(record);
    if (!modelId) return "";
    return '<h4 id="mtms-product-detail-riset">Riset ulang</h4>' +
      '<div class="pk-research" data-research="true" data-model-id="' + escapeAttr(modelId) + '">' +
      '<div class="pk-research-bar">' +
      '<button type="button" class="pk-research-start">Riset ulang</button>' +
      '<span class="pk-research-status" role="status" aria-live="polite"></span>' +
      "</div>" +
      '<div class="pk-research-candidates"></div>' +
      "</div>";
  }

  function sourceHtml(record, options) {
    var sourceUrl = safeLink(options.sourceUrl || record.source_url);
    var photoUrl = safeLink(options.photoUrl || record.photo_url);
    var canonicalUrl = safeLink(options.canonicalUrl);
    var links = [];
    if (sourceUrl) {
      links.push('<a href="' + escapeAttr(sourceUrl) + '" target="_blank" rel="noopener noreferrer">' +
        escapeHtml(options.sourceLabel || "Lihat sumber") + "</a>");
    }
    if (photoUrl && photoUrl !== sourceUrl) {
      links.push('<a href="' + escapeAttr(photoUrl) + '" target="_blank" rel="noopener noreferrer">' +
        "Sumber foto</a>");
    }
    if (canonicalUrl) {
      links.push('<a href="' + escapeAttr(canonicalUrl) + '">Buka record di katalog Produk</a>');
    }
    return '<div class="pk-detail-source">' + (links.length ? links.join("") :
      '<span class="pk-detail-missing">' + MISSING + "</span>") + "</div>";
  }

  function ensureModal() {
    if (modal) return modal;
    modal = document.createElement("div");
    modal.className = "pk-modal";
    modal.setAttribute("data-mtms-product-detail", "true");
    modal.innerHTML =
      '<div class="pk-modal-box pk-modal-wide" role="dialog" aria-modal="true" aria-labelledby="mtms-product-detail-title">' +
      '<button type="button" class="pk-modal-close" aria-label="Tutup">&times;</button>' +
      '<h3 class="pk-modal-title" id="mtms-product-detail-title"></h3>' +
      '<nav class="pk-detail-nav" aria-label="Bagian detail produk"></nav>' +
      '<div class="pk-modal-body" id="mtms-product-detail-ringkasan"></div>' +
      '<div class="pk-detail-bottom" data-detail-bottom="true" tabindex="-1">Akhir detail produk</div>' +
      "</div>";
    modal.addEventListener("click", function (event) {
      if (event.target === modal) close();
    });
    modal.querySelector(".pk-modal-close").addEventListener("click", close);
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && modal.classList.contains("open")) close();
    });
    document.body.appendChild(modal);
    return modal;
  }

  function clearSectionNavigation() {
    if (!sectionNavigationCleanup) return;
    sectionNavigationCleanup();
    sectionNavigationCleanup = null;
  }

  function wireSectionNavigation(hasSuggestions) {
    clearSectionNavigation();
    var nav = modal.querySelector(".pk-detail-nav");
    var box = modal.querySelector(".pk-modal-box");
    var sections = [
      ["Ringkasan", "mtms-product-detail-ringkasan"],
      ["Fitur", "mtms-product-detail-fitur"],
      ["Spesifikasi", "mtms-product-detail-spesifikasi"]
    ];
    if (hasSuggestions) sections.push(["Saran riset", "mtms-product-detail-saran"]);
    nav.innerHTML = '<div class="pk-detail-nav-buttons">' + sections.map(function (section, index) {
      return '<button type="button" data-detail-target="#' + section[1] + '" aria-controls="' +
        section[1] + '"' + (index === 0 ? ' class="is-active" aria-current="location"' : '') + '>' +
        section[0] + "</button>";
    }).join("") + '</div><span class="pk-detail-cue">Detail berlanjut di bawah &#8595;</span>';
    var buttons = Array.prototype.slice.call(nav.querySelectorAll("button[data-detail-target]"));
    var listeners = [];
    var scrollFrame = 0;

    function listen(node, type, handler, options) {
      node.addEventListener(type, handler, options);
      listeners.push(function () { node.removeEventListener(type, handler, options); });
    }

    function setActive(button) {
      buttons.forEach(function (candidate) {
        var active = candidate === button;
        candidate.classList.toggle("is-active", active);
        if (active) candidate.setAttribute("aria-current", "location");
        else candidate.removeAttribute("aria-current");
      });
    }

    function syncActiveFromScroll() {
      scrollFrame = 0;
      if (!buttons.length) return;
      var boxRect = box.getBoundingClientRect();
      var threshold = boxRect.top + nav.getBoundingClientRect().height + 18;
      var active = buttons[0];
      buttons.forEach(function (button) {
        var target = modal.querySelector(button.getAttribute("data-detail-target"));
        if (target && target.getBoundingClientRect().top <= threshold) active = button;
      });
      if (box.scrollTop + box.clientHeight >= box.scrollHeight - 2) active = buttons[buttons.length - 1];
      setActive(active);
    }

    function onScroll() {
      if (scrollFrame) window.cancelAnimationFrame(scrollFrame);
      scrollFrame = window.requestAnimationFrame(syncActiveFromScroll);
    }

    buttons.forEach(function (button) {
      function navigate() {
        var target = modal.querySelector(button.getAttribute("data-detail-target"));
        if (!box || !target) return;
        setActive(button);
        var targetTop = box.scrollTop + target.getBoundingClientRect().top - box.getBoundingClientRect().top;
        box.scrollTo({
          top: Math.max(0, targetTop - nav.getBoundingClientRect().height - 8),
          behavior: "auto"
        });
      }
      function onKeydown(event) {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        navigate();
      }
      listen(button, "click", navigate);
      listen(button, "keydown", onKeydown);
    });
    listen(box, "scroll", onScroll, { passive: true });
    box.scrollTop = 0;
    setActive(buttons[0]);
    sectionNavigationCleanup = function () {
      if (scrollFrame) window.cancelAnimationFrame(scrollFrame);
      listeners.forEach(function (remove) { remove(); });
    };
  }

  function wireGallery(photos) {
    var gallery = modal.querySelector(".pk-gal");
    if (!gallery) return;
    var image = gallery.querySelector(".pk-gal-img");
    var thumbs = gallery.querySelectorAll(".pk-gal-thumb");
    function select(index) {
      index = (index + photos.length) % photos.length;
      setImageSource(image, photos[index]);
      image.setAttribute("data-idx", index);
      for (var i = 0; i < thumbs.length; i++) {
        thumbs[i].classList.toggle("active", Number(thumbs[i].getAttribute("data-idx")) === index);
      }
    }
    gallery.querySelectorAll(".pk-gal-nav").forEach(function (button) {
      button.addEventListener("click", function () {
        select(Number(image.getAttribute("data-idx")) + Number(button.getAttribute("data-dir")));
      });
    });
    thumbs.forEach(function (button) {
      button.addEventListener("click", function () { select(Number(button.getAttribute("data-idx"))); });
    });
  }

  function close() {
    if (!modal || !modal.classList.contains("open")) return;
    modal.classList.remove("open");
    clearResearchPoll();
    clearSectionNavigation();
    if (previousFocus && document.contains(previousFocus) && typeof previousFocus.focus === "function") {
      previousFocus.focus();
    }
    previousFocus = null;
    unlockBody();
  }

  function open(record, options) {
    record = record || {};
    options = options || {};
    ensureModal();
    var wasOpen = modal.classList.contains("open");
    if (!wasOpen) {
      previousFocus = document.activeElement;
      lockBody();
    }

    var title = escapeHtml(display(record.model));
    title += ' <span class="pk-cat">' + escapeHtml(display(record.kategori)) + "</span>";
    if (typeof options.onEdit === "function") {
      title += '<button type="button" class="pk-modal-edit">&#9998;&#65039; Edit</button>';
    }
    modal.querySelector(".pk-modal-title").innerHTML = title;

    var priceSource = record.harga_source || record.price_source;
    var displayedPriceSource = formatPriceSource(priceSource);
    var price = hasValue(record.harga_idr) ? record.harga_idr : record.price;
    var capacityNote = record.kapasitas_catatan;
    var rows = specRowsHtml([
      { label: "Tipe pintu", value: record.door },
      { label: "Kapasitas", value: capacityValue(record), note: capacityNote },
      { label: "Rentang kapasitas", value: record.range },
      { label: "Material pintu", value: record.material },
      { label: "Daya listrik", value: hasValue(record.daya_watt) ? withUnit(record.daya_watt, "W") : "" },
      { label: "Garansi kompresor", value: hasValue(record.garansi_tahun) ? withUnit(record.garansi_tahun, "tahun") : "" },
      { label: "Warna / varian", value: listValue(record.varian) },
      { label: "Seri", value: hasValue(record.serie) ? record.serie : record.seri }
    ]);

    var photos = photoList(record);
    var sourceSection = "<h4>Sumber data</h4>" + sourceHtml(record, options);
    var featureMeta = record.fitur_meta && typeof record.fitur_meta === "object" && !Array.isArray(record.fitur_meta) ?
      provenanceHtml(record.fitur_meta, "pk-feature-provenance", true) : "";
    var featureSection = '<h4 id="mtms-product-detail-fitur">Fitur Unggulan</h4>' + featuresHtml(record) + featureMeta;
    var featureText = featureValues(record).map(String).join("; ");
    var duplicateBenefit = hasValue(record.benefit) && String(record.benefit).trim() === featureText;
    var benefitSection = hasValue(record.benefit) && !duplicateBenefit ?
      "<h4>Keunggulan &amp; Fitur</h4>" +
        '<p class="pk-benefit">' + escapeHtml(record.benefit) + "</p>" : "";
    var right = '<p class="pk-detail-brand"><strong>Brand:</strong> ' + escapeHtml(display(record.brand)) + "</p>" +
      (flagsHtml(record) ? '<div class="pk-modal-flags">' + flagsHtml(record) + "</div>" : "") +
      '<div class="pk-price-hero">' + escapeHtml(formatRupiah(price)) +
      (displayedPriceSource ? '<span class="pk-harga-src">Sumber: ' + escapeHtml(displayedPriceSource) + "</span>" : "") +
      "</div>" + sourceSection + featureSection +
      "<table><tbody>" + rows + "</tbody></table>" + benefitSection +
      '<h4 id="mtms-product-detail-spesifikasi">Spesifikasi terstruktur</h4>' +
      dynamicSpecsHtml(record, options) + suggestionsHtml(record, options) +
      researchSectionHtml(record);
    modal.querySelector(".pk-modal-body").innerHTML =
      '<div class="pk-modal-left">' + photosHtml(record, photos) + "</div>" +
      '<div class="pk-modal-right">' + right + "</div>";

    wirePhotoFallbacks(modal.querySelector(".pk-modal-left"));
    wireGallery(photos);
    wireResearch(record, options);
    wireSectionNavigation(Array.isArray(record.research_suggestions) && record.research_suggestions.length > 0);
    var edit = modal.querySelector(".pk-modal-edit");
    if (edit) {
      edit.addEventListener("click", function () {
        var handler = options.onEdit;
        close();
        window.setTimeout(function () { handler(record); }, 0);
      });
    }
    modal.classList.add("open");
    modal.querySelector(".pk-modal-close").focus();
  }

  window.MTMSProductDetail = {
    open: open,
    close: close,
    configureResearch: configureResearch,
    isOpen: function () { return !!(modal && modal.classList.contains("open")); }
  };
})(window, document);
