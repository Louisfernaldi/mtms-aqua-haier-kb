(function (window, document) {
  "use strict";

  if (window.MTMSDynamicSpecEditor) return;

  var CORE_KEYS = [
    "form_factor", "door_count", "freezer_position", "gross_capacity_l",
    "net_capacity_l", "width_mm", "height_mm", "depth_mm", "rated_power_w",
    "compressor_type", "cooling_system", "defrost_type"
  ];

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function safeUrl(value) {
    if (!value) return "";
    try {
      var parsed = new URL(String(value), window.location.href);
      return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : "";
    } catch (_error) {
      return "";
    }
  }

  function responseSha(response) {
    return String(response.headers.get("X-Data-SHA") || response.headers.get("ETag") || "")
      .trim().replace(/^W\//, "").replace(/^"|"$/g, "");
  }

  function fetchJson(url) {
    return fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (payload) {
          if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
          var sha = responseSha(response);
          if (!sha) throw new Error("API tidak memberi ETag/X-Data-SHA");
          return { payload: payload, sha: sha };
        });
      });
  }

  function cloneData(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function loadInitialData(initialData, initialSha, categoriesUrl, reader) {
    // Loader halaman adalah satu-satunya pemilik GET model. Editor hanya
    // melanjutkan ke kategori bila payload live dan SHA sudah diberikan.
    if (!initialData || !String(initialSha || "").trim()) {
      return Promise.reject(new Error("initialData live wajib punya ETag/X-Data-SHA"));
    }
    return reader(categoriesUrl).then(function (categoryResult) {
      return [{ payload: cloneData(initialData), sha: String(initialSha).trim() }, categoryResult];
    });
  }

  function flattenModels(data) {
    var rows = [];
    var seen = {};
    function append(model, fallbackBrand) {
      var brand = model && (model.brand || fallbackBrand);
      var modelId = model && (model.model_id || (brand + "::" + model.model));
      if (!brand || !model || !model.model || seen[modelId]) return;
      seen[modelId] = true;
      rows.push({ brand: brand, modelId: modelId, record: model });
    }
    if (Array.isArray(data)) {
      data.forEach(function (model) { append(model, "AQUA"); });
    } else if (data && Array.isArray(data.brands)) {
      data.brands.forEach(function (brandRow) {
        (brandRow && Array.isArray(brandRow.models) ? brandRow.models : []).forEach(function (model) {
          append(model, brandRow.brand);
        });
      });
    }
    rows.sort(function (a, b) {
      return a.brand.localeCompare(b.brand) || String(a.record.model).localeCompare(String(b.record.model));
    });
    return rows;
  }

  function valueText(value) {
    if (value === null || value === undefined) return "";
    if (typeof value === "boolean") return value ? "true" : "false";
    return String(value);
  }

  function parsedValue(text, original) {
    var cleaned = String(text).trim();
    if (!cleaned) return null;
    if (typeof original === "number" && !Number.isNaN(Number(cleaned))) return Number(cleaned);
    if (typeof original === "boolean" && /^(true|false)$/i.test(cleaned)) return cleaned.toLowerCase() === "true";
    return cleaned;
  }

  function sameJson(left, right) {
    return JSON.stringify(left) === JSON.stringify(right);
  }

  function mount(options) {
    options = options || {};
    if (document.querySelector("[data-dynamic-spec-editor-root]")) return;
    if (!/^https?:$/.test(window.location.protocol)) return;

    var state = {
      ready: false,
      data: null,
      dataSha: "",
      categories: [],
      categorySha: "",
      models: [],
      selectedModelId: "",
      tab: "model",
      busy: false
    };
    var dataUrl = options.dataUrl || "/api/kompetitor";
    var categoriesUrl = options.categoriesUrl || "/api/spec-categories";
    var initialData = options.initialData || null;
    var initialSha = String(options.initialSha || "").trim();

    var button = document.createElement("button");
    button.type = "button";
    button.className = "ds-editor-fab";
    button.disabled = true;
    button.textContent = "Editor spesifikasi";
    button.setAttribute("aria-controls", "ds-editor-shell");
    button.setAttribute("aria-expanded", "false");

    var bootStatus = document.createElement("span");
    bootStatus.className = "ds-editor-boot-status";
    bootStatus.textContent = "Editor menunggu API live...";

    var shell = document.createElement("div");
    shell.id = "ds-editor-shell";
    shell.className = "ds-editor-shell";
    shell.hidden = true;
    shell.setAttribute("data-dynamic-spec-editor-root", "true");
    shell.innerHTML =
      '<button type="button" class="ds-editor-backdrop" data-ds-close aria-label="Tutup editor"></button>' +
      '<aside class="ds-editor-panel" aria-label="Editor spesifikasi dinamis">' +
        '<header class="ds-editor-header"><div><strong>Editor spesifikasi</strong>' +
        '<small>Data live terautentikasi · simpan memakai SHA</small></div>' +
        '<button type="button" class="ds-editor-close" data-ds-close aria-label="Tutup">&times;</button></header>' +
        '<div class="ds-editor-tabs" role="tablist">' +
          '<button type="button" data-ds-tab="model" class="active">Model &amp; nilai</button>' +
          '<button type="button" data-ds-tab="categories">Kategori global</button>' +
          '<button type="button" data-ds-reload>Muat ulang kategori</button>' +
        '</div>' +
        '<p class="ds-editor-status" role="status" aria-live="polite"></p>' +
        '<div class="ds-editor-content"></div>' +
      '</aside>';

    document.body.appendChild(button);
    document.body.appendChild(bootStatus);
    document.body.appendChild(shell);

    var content = shell.querySelector(".ds-editor-content");
    var status = shell.querySelector(".ds-editor-status");

    function setStatus(message, kind) {
      status.textContent = message || "";
      status.className = "ds-editor-status" + (kind ? " " + kind : "");
    }

    function showBootError(message) {
      state.ready = false;
      button.disabled = true;
      button.setAttribute("data-live-ready", "false");
      bootStatus.textContent = "Editor nonaktif: " + message;
      bootStatus.classList.add("error");
    }

    function loadLive() {
      if (state.busy) return Promise.resolve();
      state.busy = true;
      button.disabled = true;
      bootStatus.textContent = "Editor menunggu API live...";
      bootStatus.classList.remove("error");
      setStatus("Memuat data live...", "info");
      return loadInitialData(state.data || initialData, state.dataSha || initialSha, categoriesUrl, fetchJson)
        .then(function (results) {
          var categoryPayload = results[1].payload;
          if (!categoryPayload || !Array.isArray(categoryPayload.spec_categories)) {
            throw new Error("respons kategori invalid");
          }
          state.data = results[0].payload;
          state.dataSha = results[0].sha;
          state.categories = categoryPayload.spec_categories;
          state.categorySha = results[1].sha;
          state.models = flattenModels(state.data);
          if (!state.models.length) throw new Error("model live tidak tersedia");
          if (!state.models.some(function (row) { return row.modelId === state.selectedModelId; })) {
            state.selectedModelId = state.models[0].modelId;
          }
          state.ready = true;
          state.busy = false;
          button.disabled = false;
          button.setAttribute("data-live-ready", "true");
          bootStatus.textContent = "";
          setStatus("Data live siap. Perubahan tidak akan disimpan tanpa SHA yang sama.", "ok");
          if (!shell.hidden) render();
        })
        .catch(function (error) {
          state.busy = false;
          showBootError(error.message || "API gagal");
          setStatus("Editor tetap nonaktif: " + (error.message || "API gagal"), "error");
        });
    }

    function open() {
      if (!state.ready) return;
      shell.hidden = false;
      button.setAttribute("aria-expanded", "true");
      render();
      shell.querySelector(".ds-editor-close").focus();
    }

    function close() {
      shell.hidden = true;
      button.setAttribute("aria-expanded", "false");
      button.focus();
    }

    function selectedRow() {
      return state.models.find(function (row) { return row.modelId === state.selectedModelId; });
    }

    function provenanceHtml(entry) {
      if (!entry) return '<small class="ds-provenance">Belum ada nilai/provenance.</small>';
      var source = safeUrl(entry.source_url);
      var parts = ["origin=" + escapeHtml(entry.origin || "unknown")];
      if (entry.user_locked) parts.push("user lock aktif");
      if (entry.source_kind) parts.push(escapeHtml(entry.source_kind));
      if (entry.verified_at) parts.push(escapeHtml(entry.verified_at));
      var link = source ? ' · <a href="' + escapeHtml(source) + '" target="_blank" rel="noopener noreferrer">buka sumber</a>' : "";
      return '<small class="ds-provenance">' + parts.join(" · ") + link + "</small>";
    }

    function suggestionsHtml(row) {
      var suggestions = Array.isArray(row.record.research_suggestions) ? row.record.research_suggestions : [];
      if (!suggestions.length) return '<p class="ds-empty">Belum ada research_suggestions.</p>';
      return suggestions.map(function (item, index) {
        var category = state.categories.find(function (candidate) { return candidate.key === item.key; });
        var source = safeUrl(item.source_url);
        var pending = (item.status || "pending") === "pending";
        return '<article class="ds-suggestion" data-suggestion-index="' + index + '">' +
          '<strong>' + escapeHtml(category ? category.label : item.key) + ': ' + escapeHtml(valueText(item.value)) + '</strong>' +
          '<small>Status: ' + escapeHtml(item.status || "pending") + ' · ' + escapeHtml(item.source_kind || "sumber tidak diberi jenis") + '</small>' +
          (source ? '<a href="' + escapeHtml(source) + '" target="_blank" rel="noopener noreferrer">Lihat bukti riset</a>' : "") +
          (pending ? '<div><button type="button" data-ds-suggestion="accept">Accept</button>' +
            '<button type="button" data-ds-suggestion="reject" class="danger">Reject</button></div>' : "") +
        '</article>';
      }).join("");
    }

    function featureSuggestionsHtml(row) {
      var suggestions = Array.isArray(row.record.feature_suggestions) ? row.record.feature_suggestions : [];
      if (!suggestions.length) return '<p class="ds-empty">Belum ada feature_suggestions.</p>';
      return suggestions.map(function (item, index) {
        var source = safeUrl(item.source_url);
        var pending = (item.status || "pending") === "pending";
        var bullets = Array.isArray(item.fitur) ? item.fitur : [];
        return '<article class="ds-suggestion" data-feature-suggestion-index="' + index + '">' +
          '<strong>Usulan Fitur Unggulan: ' + escapeHtml(bullets.join(" · ") || "(kosong)") + '</strong>' +
          '<small>Status: ' + escapeHtml(item.status || "pending") + ' · ' + escapeHtml(item.source_kind || "sumber tidak diberi jenis") + '</small>' +
          (source ? '<a href="' + escapeHtml(source) + '" target="_blank" rel="noopener noreferrer">Lihat bukti riset fitur</a>' : "") +
          (pending ? '<div><button type="button" data-ds-feature-suggestion="accept">Accept fitur</button>' +
            '<button type="button" data-ds-feature-suggestion="reject" class="danger">Reject fitur</button></div>' : "") +
        '</article>';
      }).join("");
    }

    function renderModel() {
      var row = selectedRow();
      if (!row) {
        content.innerHTML = '<p class="ds-empty">Model tidak ditemukan.</p>';
        return;
      }
      var values = row.record.spec_values && typeof row.record.spec_values === "object" ? row.record.spec_values : {};
      var optionsHtml = state.models.map(function (candidate) {
        return '<option value="' + escapeHtml(candidate.modelId) + '"' +
          (candidate.modelId === row.modelId ? " selected" : "") + '>' +
          escapeHtml(candidate.brand + " · " + candidate.record.model) + '</option>';
      }).join("");
      var specsHtml = state.categories.slice().sort(function (a, b) { return a.order - b.order; }).map(function (category) {
        var entry = values[category.key];
        var raw = entry ? entry.value : null;
        return '<label class="ds-spec-row' + (category.active ? "" : " inactive") + '">' +
          '<span><strong>' + escapeHtml(category.label) + '</strong>' +
          '<code>' + escapeHtml(category.key) + '</code>' + (category.active ? "" : '<em>nonaktif</em>') + '</span>' +
          '<input type="text" data-ds-spec-key="' + escapeHtml(category.key) + '" value="' + escapeHtml(valueText(raw)) + '"' +
          ' data-original="' + escapeHtml(JSON.stringify(raw)) + '" aria-label="Nilai ' + escapeHtml(category.label) + '">' +
          '<span class="ds-unit">' + escapeHtml(category.unit && category.unit !== "-" ? category.unit : "") + '</span>' +
          provenanceHtml(entry) +
        '</label>';
      }).join("");
      var fitur = Array.isArray(row.record.fitur) ? row.record.fitur : [];
      var fiturMeta = row.record.fitur_meta && typeof row.record.fitur_meta === "object" ? row.record.fitur_meta : null;
      content.innerHTML =
        '<section data-ds-view="model"><label class="ds-field">Exact model' +
          '<select data-ds-model-select>' + optionsHtml + '</select></label>' +
          '<p class="ds-model-id">model_id: <code>' + escapeHtml(row.modelId) + '</code></p>' +
          '<div class="ds-spec-list">' + specsHtml + '</div>' +
          '<label class="ds-field">Fitur Unggulan <small>satu bullet per baris</small>' +
            '<textarea rows="6" data-ds-features data-original="' + escapeHtml(JSON.stringify(fitur)) + '">' +
            escapeHtml(fitur.join("\n")) + '</textarea>' + provenanceHtml(fiturMeta) + '</label>' +
          '<div class="ds-editor-actions"><button type="button" data-ds-save-model>Simpan nilai &amp; bullet</button></div>' +
          '<section class="ds-suggestions"><h3>Provenance &amp; research_suggestions</h3>' + suggestionsHtml(row) +
          '<h3>Feature suggestions</h3>' + featureSuggestionsHtml(row) + '</section>' +
        '</section>';
    }

    function categoryCard(category) {
      var core = CORE_KEYS.indexOf(category.key) !== -1;
      return '<form class="ds-category-card" data-ds-category-key="' + escapeHtml(category.key) + '">' +
        '<div><strong>' + escapeHtml(category.label) + '</strong><code>' + escapeHtml(category.key) + '</code>' +
          (core ? '<em>core terkunci</em>' : '') + '</div>' +
        '<label>Label<input name="label" value="' + escapeHtml(category.label) + '"></label>' +
        '<label>Grup<input name="group" value="' + escapeHtml(category.group) + '"></label>' +
        '<label>Unit<input name="unit" value="' + escapeHtml(category.unit == null ? "" : category.unit) + '"></label>' +
        '<label>Urutan<input name="order" type="number" value="' + category.order + '"' + (core ? ' disabled' : '') + '></label>' +
        '<label class="ds-check"><input name="active" type="checkbox"' + (category.active ? ' checked' : '') + (core ? ' disabled' : '') + '> Aktif</label>' +
        '<label class="ds-check"><input name="comparison" type="checkbox"' + (category.comparison ? ' checked' : '') + (core ? ' disabled' : '') + '> Comparison</label>' +
        '<button type="submit">Simpan kategori</button>' +
      '</form>';
    }

    function renderCategories() {
      var nextOrder = state.categories.reduce(function (largest, item) { return Math.max(largest, item.order); }, 120) + 10;
      content.innerHTML =
        '<section data-ds-view="categories"><p class="ds-help">Key tidak dapat diganti atau dihapus agar nilai model tidak menjadi orphan. Core tetap aktif, comparison, dan urut 10–120.</p>' +
        '<form class="ds-category-create" data-ds-create-category><h3>Tambah kategori global</h3>' +
          '<label>Key<input name="key" placeholder="contoh: ice_maker" required pattern="[a-z][a-z0-9_]*"></label>' +
          '<label>Label<input name="label" required></label>' +
          '<label>Grup<input name="group" value="Tambahan" required></label>' +
          '<label>Unit<input name="unit" value="-"></label>' +
          '<label>Urutan<input name="order" type="number" value="' + nextOrder + '" required></label>' +
          '<label class="ds-check"><input name="active" type="checkbox" checked> Aktif</label>' +
          '<label class="ds-check"><input name="comparison" type="checkbox"> Comparison</label>' +
          '<button type="submit">Tambah kategori</button></form>' +
        '<div class="ds-category-list">' + state.categories.slice().sort(function (a, b) { return a.order - b.order; }).map(categoryCard).join("") + '</div></section>';
    }

    function render() {
      shell.querySelectorAll("[data-ds-tab]").forEach(function (tab) {
        tab.classList.toggle("active", tab.getAttribute("data-ds-tab") === state.tab);
      });
      if (state.tab === "categories") renderCategories();
      else renderModel();
    }

    function patch(url, sha, payload) {
      state.busy = true;
      shell.querySelectorAll("button, input, textarea, select").forEach(function (control) { control.disabled = true; });
      setStatus("Menyimpan dengan If-Match " + sha.slice(0, 8) + "...", "info");
      return fetch(url, {
        method: "PATCH",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "If-Match": '"' + sha + '"' },
        body: JSON.stringify(payload)
      }).then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (data) {
          if (!response.ok) {
            var error = new Error(data.error || ("HTTP " + response.status));
            error.status = response.status;
            throw error;
          }
          return { data: data, sha: responseSha(response) || data.sha };
        });
      }).finally(function () { state.busy = false; });
    }

    function handleWriteError(error) {
      if (error.status === 412) {
        setStatus("STALE SHA: data berubah di tempat lain. Perubahan tidak ditulis; tekan Muat ulang.", "error");
      } else if (error.status === 401) {
        setStatus("Sesi login habis. Login ulang sebelum mengedit.", "error");
      } else {
        setStatus("Gagal menyimpan: " + (error.message || "error tidak dikenal"), "error");
      }
      render();
    }

    function saveModel() {
      var row = selectedRow();
      if (!row || state.busy) return;
      var changes = {};
      content.querySelectorAll("[data-ds-spec-key]").forEach(function (input) {
        var original = JSON.parse(input.getAttribute("data-original"));
        var next = parsedValue(input.value, original);
        if (!sameJson(original, next)) changes[input.getAttribute("data-ds-spec-key")] = { value: next };
      });
      var featuresInput = content.querySelector("[data-ds-features]");
      var originalFeatures = JSON.parse(featuresInput.getAttribute("data-original"));
      var nextFeatures = featuresInput.value.split("\n").map(function (line) { return line.trim(); }).filter(Boolean);
      var payload = { action: "update_model", model_id: row.modelId };
      if (Object.keys(changes).length) payload.spec_values = changes;
      if (!sameJson(originalFeatures, nextFeatures)) payload.fitur = nextFeatures;
      if (!payload.spec_values && !Object.prototype.hasOwnProperty.call(payload, "fitur")) {
        setStatus("Tidak ada perubahan model untuk disimpan.", "info");
        return;
      }
      patch(dataUrl, state.dataSha, payload).then(function (result) {
        state.dataSha = result.sha;
        Object.keys(row.record).forEach(function (key) { delete row.record[key]; });
        Object.assign(row.record, result.data.model);
        setStatus("Model tersimpan. Nilai dan bullet user ditandai origin=user serta user lock aktif.", "ok");
        renderModel();
      }).catch(handleWriteError);
    }

    function decideSuggestion(buttonElement) {
      var row = selectedRow();
      var card = buttonElement.closest("[data-suggestion-index]");
      if (!row || !card || state.busy) return;
      var decision = buttonElement.getAttribute("data-ds-suggestion");
      patch(dataUrl, state.dataSha, {
        action: decision === "accept" ? "accept_suggestion" : "reject_suggestion",
        model_id: row.modelId,
        suggestion_index: Number(card.getAttribute("data-suggestion-index"))
      }).then(function (result) {
        state.dataSha = result.sha;
        Object.keys(row.record).forEach(function (key) { delete row.record[key]; });
        Object.assign(row.record, result.data.model);
        setStatus("Suggestion di-" + (decision === "accept" ? "accept" : "reject") + " secara eksplisit.", "ok");
        renderModel();
      }).catch(handleWriteError);
    }

    function decideFeatureSuggestion(buttonElement) {
      var row = selectedRow();
      var card = buttonElement.closest("[data-feature-suggestion-index]");
      if (!row || !card || state.busy) return;
      var decision = buttonElement.getAttribute("data-ds-feature-suggestion");
      patch(dataUrl, state.dataSha, {
        action: decision === "accept" ? "accept_feature_suggestion" : "reject_feature_suggestion",
        model_id: row.modelId,
        suggestion_index: Number(card.getAttribute("data-feature-suggestion-index"))
      }).then(function (result) {
        state.dataSha = result.sha;
        Object.keys(row.record).forEach(function (key) { delete row.record[key]; });
        Object.assign(row.record, result.data.model);
        setStatus("Feature suggestion di-" + (decision === "accept" ? "accept" : "reject") + " secara eksplisit.", "ok");
        renderModel();
      }).catch(handleWriteError);
    }

    function categoryPayload(form) {
      return {
        label: form.elements.label.value.trim(),
        group: form.elements.group.value.trim(),
        unit: form.elements.unit.value.trim(),
        order: Number(form.elements.order.value),
        active: form.elements.active.checked,
        comparison: form.elements.comparison.checked
      };
    }

    function saveCategory(form) {
      if (state.busy) return;
      var key = form.getAttribute("data-ds-category-key");
      var patchData = categoryPayload(form);
      patch(categoriesUrl, state.categorySha, { action: "update_category", key: key, patch: patchData })
        .then(function (result) {
          state.categorySha = result.sha;
          state.categories = result.data.spec_categories;
          setStatus("Kategori global tersimpan.", "ok");
          renderCategories();
        }).catch(handleWriteError);
    }

    function createCategory(form) {
      if (state.busy) return;
      var category = categoryPayload(form);
      category.key = form.elements.key.value.trim();
      patch(categoriesUrl, state.categorySha, { action: "create_category", category: category })
        .then(function (result) {
          state.categorySha = result.sha;
          state.categories = result.data.spec_categories;
          setStatus("Kategori global ditambahkan tanpa membuat value yatim.", "ok");
          renderCategories();
        }).catch(handleWriteError);
    }

    button.addEventListener("click", open);
    shell.addEventListener("click", function (event) {
      if (event.target.closest("[data-ds-close]")) close();
      var tab = event.target.closest("[data-ds-tab]");
      if (tab) { state.tab = tab.getAttribute("data-ds-tab"); render(); }
      if (event.target.closest("[data-ds-reload]")) loadLive();
      if (event.target.closest("[data-ds-save-model]")) saveModel();
      var suggestion = event.target.closest("[data-ds-suggestion]");
      if (suggestion) decideSuggestion(suggestion);
      var featureSuggestion = event.target.closest("[data-ds-feature-suggestion]");
      if (featureSuggestion) decideFeatureSuggestion(featureSuggestion);
    });
    shell.addEventListener("change", function (event) {
      if (event.target.matches("[data-ds-model-select]")) {
        state.selectedModelId = event.target.value;
        renderModel();
      }
    });
    shell.addEventListener("submit", function (event) {
      event.preventDefault();
      if (event.target.matches("[data-ds-create-category]")) createCategory(event.target);
      if (event.target.matches("[data-ds-category-key]")) saveCategory(event.target);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !shell.hidden) close();
    });

    loadLive();
  }

  window.MTMSDynamicSpecEditor = { mount: mount, _loadInitialData: loadInitialData, _flattenModels: flattenModels };
})(window, document);
