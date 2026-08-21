(function (window, document) {
  "use strict";

  if (window.MTMSProductDetail && typeof window.MTMSProductDetail.open === "function") return;

  var MISSING = "Belum tersedia";
  var FAILED_IMAGE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480"><rect width="640" height="480" fill="#f4f8fb"/><g fill="none" stroke="#718096" stroke-width="12"><rect x="220" y="112" width="200" height="164" rx="16"/><path d="m240 252 58-62 48 48 30-32 44 46"/><circle cx="368" cy="158" r="18"/></g><text x="320" y="350" fill="#52606d" font-family="Arial,sans-serif" font-size="28" text-anchor="middle">Foto gagal dimuat</text></svg>';
  var FAILED_IMAGE_SRC = "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(FAILED_IMAGE_SVG);
  var modal = null;
  var bodyLockState = null;
  var previousFocus = null;

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
    if (/^(?:https?:\/\/|\/|\.\.?\/)/i.test(url)) return url;
    if (!/^[a-z][a-z0-9+.-]*:/i.test(url)) return url;
    return "";
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
    var features = Array.isArray(record.fitur) ? record.fitur.filter(hasValue) : [];
    if (!features.length && Array.isArray(record.features)) {
      features = record.features.filter(hasValue);
    }
    if (!features.length) return '<p class="pk-benefit pk-detail-missing">' + MISSING + "</p>";
    return '<ul class="pk-fitur">' + features.map(function (feature) {
      return "<li>" + escapeHtml(feature) + "</li>";
    }).join("") + "</ul>";
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
      '<div class="pk-modal-body"></div>' +
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
    var featureSection = "<h4>Fitur Unggulan</h4>" + featuresHtml(record);
    var benefitSection = hasValue(record.benefit) ?
      "<h4>Keunggulan &amp; Fitur</h4>" +
        '<p class="pk-benefit">' + escapeHtml(record.benefit) + "</p>" : "";
    var right = '<p class="pk-detail-brand"><strong>Brand:</strong> ' + escapeHtml(display(record.brand)) + "</p>" +
      (flagsHtml(record) ? '<div class="pk-modal-flags">' + flagsHtml(record) + "</div>" : "") +
      '<div class="pk-price-hero">' + escapeHtml(formatRupiah(price)) +
      (displayedPriceSource ? '<span class="pk-harga-src">Sumber: ' + escapeHtml(displayedPriceSource) + "</span>" : "") +
      "</div>" + sourceSection + featureSection +
      "<table><tbody>" + rows + "</tbody></table>" + benefitSection;
    modal.querySelector(".pk-modal-body").innerHTML =
      '<div class="pk-modal-left">' + photosHtml(record, photos) + "</div>" +
      '<div class="pk-modal-right">' + right + "</div>";

    wirePhotoFallbacks(modal.querySelector(".pk-modal-left"));
    wireGallery(photos);
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

  window.MTMSProductDetail = { open: open, close: close };
})(window, document);
