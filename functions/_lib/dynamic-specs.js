// Shared helpers for dynamic-spec Pages Functions.
// Pure mutation helpers are exported so endpoint behavior can be proven offline.

export const CORE_CATEGORY_KEYS = [
  "form_factor",
  "door_count",
  "freezer_position",
  "gross_capacity_l",
  "net_capacity_l",
  "width_mm",
  "height_mm",
  "depth_mm",
  "rated_power_w",
  "compressor_type",
  "cooling_system",
  "defrost_type",
];

const CATEGORY_FIELDS = ["key", "label", "group", "unit", "comparison", "order", "active"];
const MUTABLE_CATEGORY_FIELDS = ["label", "group", "unit", "comparison", "order", "active"];
const ALLOWED_ACTIONS = new Set([
  "set_spec_value",
  "set_features",
  "update_model",
  "submit_research",
  "accept_suggestion",
  "reject_suggestion",
  "submit_research_features",
  "accept_feature_suggestion",
  "reject_feature_suggestion",
]);

export class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "HttpError";
    this.status = status;
  }
}

function own(value, key) {
  return Object.prototype.hasOwnProperty.call(value, key);
}

export const DOCUMENT_LIMITS = Object.freeze({
  maxDocumentBytes: 2 * 1024 * 1024,
  maxStringLength: 512 * 1024,
  maxKeyLength: 128,
  maxArrayLength: 5000,
  maxObjectKeys: 500,
  maxDepth: 20,
  maxNodes: 50000,
  maxBrands: 50,
  maxModels: 5000,
  maxBrandLength: 80,
  maxModelLength: 200,
});

export async function readJsonBodyCapped(request, maxBytes = DOCUMENT_LIMITS.maxDocumentBytes) {
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 0) {
    throw new HttpError(400, "body size limit invalid");
  }

  const contentLength = request && request.headers && request.headers.get("Content-Length");
  if (contentLength !== null) {
    if (!/^\d+$/.test(contentLength)) throw new HttpError(400, "Content-Length invalid");
    if (Number(contentLength) > maxBytes) throw new HttpError(413, "request body terlalu besar");
  }

  if (!request || !request.body || typeof request.body.getReader !== "function") {
    throw new HttpError(400, "body stream invalid");
  }

  let reader;
  const decoder = new TextDecoder("utf-8", { fatal: true });
  const parts = [];
  let totalBytes = 0;
  try {
    reader = request.body.getReader();
    while (true) {
      const result = await reader.read();
      if (!result || typeof result.done !== "boolean") throw new Error("invalid stream result");
      if (result.done) break;
      if (!(result.value instanceof Uint8Array)) throw new Error("invalid stream chunk");
      totalBytes += result.value.byteLength;
      if (totalBytes > maxBytes) {
        try {
          await reader.cancel("request body terlalu besar");
        } catch (_cancelError) {
          // The 413 result must not depend on whether the producer accepts cancellation.
        }
        throw new HttpError(413, "request body terlalu besar");
      }
      parts.push(decoder.decode(result.value, { stream: true }));
    }
    parts.push(decoder.decode());
  } catch (error) {
    if (error instanceof HttpError) throw error;
    throw new HttpError(400, "body stream invalid");
  } finally {
    if (reader) {
      try {
        reader.releaseLock();
      } catch (_releaseError) {
        // A failed release does not change the already determined parse result.
      }
    }
  }

  try {
    return JSON.parse(parts.join(""));
  } catch (_error) {
    throw new HttpError(400, "malformed JSON");
  }
}

function utf8ByteLength(value) {
  return new TextEncoder().encode(String(value)).length;
}

// Recursive bounds run before every JSON clone and before writeGithubJson
// serializes/base64-encodes a document. The byte counter matches compact JSON
// without first materializing the whole serialized document.
export function validateRecursiveBounds(value, overrides = {}) {
  const limits = { ...DOCUMENT_LIMITS, ...overrides };
  const ancestors = new WeakSet();
  let nodes = 0;
  let serializedBytes = 0;
  let brands = 0;
  let models = 0;

  function addBytes(amount) {
    serializedBytes += amount;
    if (serializedBytes > limits.maxDocumentBytes) {
      throw new HttpError(413, "serialized document terlalu besar");
    }
  }

  function visit(current, depth, field) {
    if (depth > limits.maxDepth) throw new HttpError(413, "document depth terlalu dalam");
    nodes += 1;
    if (nodes > limits.maxNodes) throw new HttpError(413, "document nodes terlalu banyak");

    if (current === null) {
      addBytes(4);
      return;
    }
    if (typeof current === "string") {
      if (current.length > limits.maxStringLength) throw new HttpError(413, "string terlalu panjang");
      if (field === "brand" && current.length > limits.maxBrandLength) {
        throw new HttpError(413, "brand terlalu panjang");
      }
      if ((field === "model" || field === "model_id") && current.length > limits.maxModelLength) {
        throw new HttpError(413, "model terlalu panjang");
      }
      addBytes(utf8ByteLength(JSON.stringify(current)));
      return;
    }
    if (typeof current === "number") {
      if (!Number.isFinite(current)) throw new HttpError(400, "angka document tidak valid");
      addBytes(utf8ByteLength(JSON.stringify(current)));
      return;
    }
    if (typeof current === "boolean") {
      addBytes(current ? 4 : 5);
      return;
    }
    if (typeof current !== "object") throw new HttpError(400, "tipe document tidak didukung");
    if (ancestors.has(current)) throw new HttpError(400, "document circular tidak didukung");
    ancestors.add(current);

    if (Array.isArray(current)) {
      if (current.length > limits.maxArrayLength) throw new HttpError(413, "array terlalu panjang");
      if (field === "brands") {
        brands += current.length;
        if (brands > limits.maxBrands) throw new HttpError(413, "brand terlalu banyak");
      }
      if (field === "models") {
        models += current.length;
        if (models > limits.maxModels) throw new HttpError(413, "model terlalu banyak");
      }
      addBytes(2 + Math.max(0, current.length - 1));
      current.forEach(function (item) { visit(item, depth + 1, ""); });
    } else {
      const keys = Object.keys(current);
      if (keys.length > limits.maxObjectKeys) throw new HttpError(413, "object keys terlalu banyak");
      addBytes(2 + Math.max(0, keys.length - 1));
      keys.forEach(function (key) {
        if (key.length > limits.maxKeyLength) throw new HttpError(413, "key terlalu panjang");
        addBytes(utf8ByteLength(JSON.stringify(key)) + 1);
        visit(current[key], depth + 1, key);
      });
    }
    ancestors.delete(current);
  }

  if (Array.isArray(value) && value.some(function (item) {
    return item && typeof item === "object" && own(item, "model");
  })) {
    models = value.length;
    if (models > limits.maxModels) throw new HttpError(413, "model terlalu banyak");
  }
  visit(value, 0, "");
  return { serializedBytes, brands, models, nodes };
}

function clone(value) {
  validateRecursiveBounds(value);
  return JSON.parse(JSON.stringify(value));
}

function cleanText(value, field, maxLength, allowEmpty = false) {
  if (typeof value !== "string") throw new HttpError(400, field + " harus teks");
  const result = value.trim();
  if (!allowEmpty && !result) throw new HttpError(400, field + " wajib diisi");
  if (result.length > maxLength) throw new HttpError(400, field + " terlalu panjang");
  return result;
}

function validHttpUrl(value) {
  if (typeof value !== "string" || !value.trim()) return false;
  try {
    const parsed = new URL(value);
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && Boolean(parsed.hostname);
  } catch (_error) {
    return false;
  }
}

function validStoredUrl(value) {
  if (typeof value !== "string" || !value.trim()) return false;
  const candidate = value.trim();
  if (/[\u0000-\u001f\u007f\\]/.test(candidate) || candidate.startsWith("//")) return false;
  if (!/^[a-z][a-z0-9+.-]*:/i.test(candidate)) return true;
  return validHttpUrl(candidate);
}

function validateStoredUrlState(model) {
  ["foto", "image", "photo", "photo_url", "source_url"].forEach(function (field) {
    if (!own(model, field) || model[field] == null || model[field] === "") return;
    if (!validStoredUrl(model[field])) {
      throw new HttpError(400, field + " invalid: wajib http/https atau path relatif situs");
    }
  });
  if (!own(model, "foto_list")) return;
  if (!Array.isArray(model.foto_list)) throw new HttpError(400, "foto_list wajib array");
  model.foto_list.forEach(function (url) {
    if (!validStoredUrl(url)) {
      throw new HttpError(400, "foto_list invalid: wajib http/https atau path relatif situs");
    }
  });
}

function validTimestamp(value) {
  if (typeof value !== "string" || !value.trim()) return false;
  if (!/(?:Z|[+-]\d\d:\d\d)$/.test(value.trim())) return false;
  return !Number.isNaN(Date.parse(value));
}

function normalizeScalar(value) {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed.length > 1000) throw new HttpError(400, "value terlalu panjang");
    return trimmed || null;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new HttpError(400, "value angka tidak valid");
    return value;
  }
  if (typeof value === "boolean") return value;
  throw new HttpError(400, "value harus teks, angka, boolean, atau null");
}

function validateProvenance(entry, requireResearch) {
  const sourceUrl = entry.source_url == null || entry.source_url === "" ? null : entry.source_url;
  const sourceKind = entry.source_kind == null || entry.source_kind === "" ? null : entry.source_kind;
  const verifiedAt = entry.verified_at == null || entry.verified_at === "" ? null : entry.verified_at;

  if (sourceUrl !== null && !validHttpUrl(sourceUrl)) {
    throw new HttpError(400, "source_url invalid: wajib http/https");
  }
  if (sourceKind !== null) cleanText(sourceKind, "source_kind", 80);
  if (verifiedAt !== null && !validTimestamp(verifiedAt)) {
    throw new HttpError(400, "verified_at invalid: wajib timestamp bertimezone");
  }
  if (sourceUrl !== null && sourceKind === null) {
    throw new HttpError(400, "source_url wajib punya source_kind");
  }
  if (verifiedAt !== null && sourceUrl === null) {
    throw new HttpError(400, "verified_at wajib punya source_url");
  }
  if (requireResearch && (!sourceUrl || !sourceKind || !verifiedAt)) {
    throw new HttpError(400, "nilai research wajib source_url, source_kind, dan verified_at");
  }
  return { source_url: sourceUrl, source_kind: sourceKind, verified_at: verifiedAt };
}

export function categoryItems(document) {
  if (Array.isArray(document)) return document;
  if (document && Array.isArray(document.spec_categories)) return document.spec_categories;
  throw new HttpError(400, "dokumen kategori wajib {spec_categories: [...]}");
}

export function validateCategoryDocument(document) {
  const items = categoryItems(document);
  if (items.length < CORE_CATEGORY_KEYS.length || items.length > 200) {
    throw new HttpError(400, "jumlah kategori invalid");
  }
  const keys = new Set();
  const orders = new Set();
  let previousOrder = -Infinity;
  items.forEach(function (item, index) {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      throw new HttpError(400, "category[" + index + "] harus object");
    }
    CATEGORY_FIELDS.forEach(function (field) {
      if (!own(item, field)) throw new HttpError(400, "category[" + index + "] kurang field " + field);
    });
    const key = cleanText(item.key, "key", 64);
    if (!/^[a-z][a-z0-9_]*$/.test(key)) throw new HttpError(400, "key kategori invalid");
    if (keys.has(key)) throw new HttpError(409, "duplicate key kategori / key kategori duplikat");
    keys.add(key);
    cleanText(item.label, "label", 120);
    cleanText(item.group, "group", 80);
    if (item.unit !== null && typeof item.unit !== "string") throw new HttpError(400, "unit invalid");
    if (typeof item.unit === "string" && item.unit.length > 40) throw new HttpError(400, "unit terlalu panjang");
    if (typeof item.comparison !== "boolean") throw new HttpError(400, "comparison wajib boolean");
    if (typeof item.active !== "boolean") throw new HttpError(400, "active wajib boolean");
    if (!Number.isInteger(item.order)) throw new HttpError(400, "order wajib integer");
    if (orders.has(item.order)) throw new HttpError(409, "order kategori duplikat");
    if (item.order <= previousOrder) throw new HttpError(400, "order kategori wajib menaik");
    orders.add(item.order);
    previousOrder = item.order;
  });

  CORE_CATEGORY_KEYS.forEach(function (key, index) {
    const item = items[index];
    if (!item || item.key !== key) throw new HttpError(400, "kategori inti tidak boleh rename, hapus, atau diurut ulang");
    if (item.order !== (index + 1) * 10) throw new HttpError(400, "order kategori inti wajib 10..120");
    if (item.active !== true || item.comparison !== true) {
      throw new HttpError(400, "kategori inti wajib active dan comparison");
    }
  });
  items.slice(CORE_CATEGORY_KEYS.length).forEach(function (item) {
    if (item.order <= 120) throw new HttpError(400, "order kategori tambahan wajib di atas kategori inti");
  });
  return document;
}

function normalizedCategory(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new HttpError(400, "category wajib object");
  }
  const key = cleanText(raw.key, "key", 64);
  if (!/^[a-z][a-z0-9_]*$/.test(key)) throw new HttpError(400, "key kategori invalid");
  const order = Number(raw.order);
  if (!Number.isInteger(order)) throw new HttpError(400, "order wajib integer");
  return {
    key,
    label: cleanText(raw.label, "label", 120),
    group: cleanText(raw.group, "group", 80),
    unit: raw.unit == null ? null : cleanText(raw.unit, "unit", 40, true),
    comparison: raw.comparison === true,
    order,
    active: raw.active !== false,
  };
}

export function mutateCategories(document, operation) {
  validateCategoryDocument(document);
  const result = clone(document);
  const items = categoryItems(result);
  if (!operation || typeof operation !== "object") throw new HttpError(400, "invalid input");

  if (operation.action === "create_category") {
    const item = normalizedCategory(operation.category);
    if (CORE_CATEGORY_KEYS.includes(item.key)) throw new HttpError(409, "duplicate key kategori inti");
    if (items.some(function (current) { return current.key === item.key; })) {
      throw new HttpError(409, "duplicate key kategori / key kategori duplikat");
    }
    items.push(item);
  } else if (operation.action === "update_category") {
    const key = cleanText(operation.key, "key", 64);
    const item = items.find(function (current) { return current.key === key; });
    if (!item) throw new HttpError(404, "kategori tidak ditemukan");
    const patch = operation.patch;
    if (!patch || typeof patch !== "object" || Array.isArray(patch)) throw new HttpError(400, "patch invalid");
    if (own(patch, "key") && patch.key !== key) {
      throw new HttpError(400, "key kategori immutable agar tidak membuat orphan");
    }
    Object.keys(patch).forEach(function (field) {
      if (field !== "key" && !MUTABLE_CATEGORY_FIELDS.includes(field)) {
        throw new HttpError(400, "field kategori tidak dikenal: " + field);
      }
    });
    MUTABLE_CATEGORY_FIELDS.forEach(function (field) {
      if (own(patch, field)) item[field] = patch[field];
    });
    if (CORE_CATEGORY_KEYS.includes(key)) {
      const coreIndex = CORE_CATEGORY_KEYS.indexOf(key);
      if (item.order !== (coreIndex + 1) * 10 || item.active !== true || item.comparison !== true) {
        throw new HttpError(400, "kategori inti tidak boleh dinonaktifkan, dikeluarkan dari comparison, atau diurut ulang");
      }
    }
  } else {
    throw new HttpError(400, "invalid action kategori");
  }

  items.sort(function (a, b) { return a.order - b.order || a.key.localeCompare(b.key); });
  validateCategoryDocument(result);
  return result;
}

function modelRows(document) {
  const rows = [];
  if (Array.isArray(document)) {
    document.forEach(function (model) {
      if (model && typeof model === "object") rows.push({ brand: model.brand || "AQUA", model });
    });
    return rows;
  }
  if (document && Array.isArray(document.brands)) {
    document.brands.forEach(function (brandRow) {
      if (!brandRow || !Array.isArray(brandRow.models)) return;
      brandRow.models.forEach(function (model) {
        if (model && typeof model === "object") rows.push({ brand: brandRow.brand, model });
      });
    });
    return rows;
  }
  throw new HttpError(400, "dokumen model invalid");
}

function stableSerialize(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(stableSerialize).join(",") + "]";
  return "{" + Object.keys(value).sort().map(function (key) {
    return JSON.stringify(key) + ":" + stableSerialize(value[key]);
  }).join(",") + "}";
}

function sameJson(left, right) {
  return stableSerialize(left) === stableSerialize(right);
}

function transitionRows(document) {
  const seen = new Set();
  return modelRows(document).map(function (row) {
    if (typeof row.brand !== "string" || !row.brand.trim()) throw new HttpError(400, "brand wajib diisi");
    if (!row.model || typeof row.model.model !== "string" || !row.model.model.trim()) {
      throw new HttpError(400, "model wajib diisi");
    }
    const id = exactModelId(row.brand, row.model);
    if (seen.has(id)) throw new HttpError(409, "model_id duplikat: " + id);
    seen.add(id);
    return { id, brand: row.brand, model: row.model };
  });
}

function envelopeMetadata(document) {
  const result = {};
  Object.keys(document).forEach(function (key) {
    if (key !== "brands" && key !== "groups") result[key] = document[key];
  });
  result.brands = document.brands.map(function (brandRow) {
    const metadata = {};
    Object.keys(brandRow).forEach(function (key) {
      if (key !== "models") metadata[key] = brandRow[key];
    });
    return metadata;
  });
  return result;
}

function expectedOrder(beforeRows, afterRows, operation) {
  const before = beforeRows.map(function (row) { return row.id; });
  const after = afterRows.map(function (row) { return row.id; });
  if (operation.type === "add") {
    return sameJson(after.filter(function (id) { return id !== operation.after.id; }), before);
  }
  if (operation.type === "delete") {
    return sameJson(before.filter(function (id) { return id !== operation.before.id; }), after);
  }
  if (operation.type === "rename") {
    return sameJson(before.map(function (id) {
      return id === operation.before.id ? operation.after.id : id;
    }), after);
  }
  return sameJson(before, after);
}

function groupsAfterDelete(groups, operation) {
  const result = clone(groups);
  if (operation.before.brand === "AQUA") {
    return result.filter(function (group) { return !group || group.aqua !== operation.before.model.model; });
  }
  result.forEach(function (group) {
    if (group && group.competitors && group.competitors[operation.before.brand] === operation.before.model.model) {
      delete group.competitors[operation.before.brand];
    }
  });
  return result;
}

function groupsAfterRename(groups, operation) {
  const result = clone(groups);
  result.forEach(function (group) {
    if (!group) return;
    if (operation.before.brand === "AQUA" && group.aqua === operation.before.model.model) {
      group.aqua = operation.after.model.model;
    }
    if (operation.before.brand !== "AQUA" && group.competitors &&
      group.competitors[operation.before.brand] === operation.before.model.model) {
      group.competitors[operation.before.brand] = operation.after.model.model;
    }
  });
  return result;
}

function allowedAddGroups(beforeGroups, afterGroups, operation) {
  if (sameJson(beforeGroups, afterGroups)) return true;
  if (operation.after.brand === "AQUA") {
    return sameJson(afterGroups, beforeGroups.concat([{
      aqua: operation.after.model.model,
      competitors: {},
    }]));
  }
  if (beforeGroups.length !== afterGroups.length) return false;
  let changed = 0;
  for (let index = 0; index < beforeGroups.length; index += 1) {
    if (sameJson(beforeGroups[index], afterGroups[index])) continue;
    const expected = clone(beforeGroups[index]);
    if (!expected || typeof expected !== "object" || Array.isArray(expected)) return false;
    if (!expected.competitors || typeof expected.competitors !== "object" || Array.isArray(expected.competitors)) {
      expected.competitors = {};
    }
    if (own(expected.competitors, operation.after.brand)) return false;
    expected.competitors[operation.after.brand] = operation.after.model.model;
    if (!sameJson(expected, afterGroups[index])) return false;
    changed += 1;
  }
  return changed === 1;
}

function validateGroupTransition(beforeDocument, afterDocument, operation) {
  if (Array.isArray(beforeDocument)) return;
  const beforeGroups = beforeDocument.groups == null ? [] : beforeDocument.groups;
  const afterGroups = afterDocument.groups == null ? [] : afterDocument.groups;
  if (!Array.isArray(beforeGroups) || !Array.isArray(afterGroups)) {
    throw new HttpError(400, "groups wajib array");
  }
  let valid = false;
  if (operation.type === "edit") valid = sameJson(beforeGroups, afterGroups);
  if (operation.type === "delete") valid = sameJson(groupsAfterDelete(beforeGroups, operation), afterGroups);
  if (operation.type === "rename") valid = sameJson(groupsAfterRename(beforeGroups, operation), afterGroups);
  if (operation.type === "add") valid = allowedAddGroups(beforeGroups, afterGroups, operation);
  if (!valid) throw new HttpError(400, "groups/legacy metadata berubah di luar satu operasi UI");
}

// Pure full-document guard shared by PUT Produk and PUT Kompetitor. It accepts
// exactly one model add/delete/rename/edit while preserving every unaffected
// model plus envelope/brand metadata and only the matching group references.
export function validateDocumentTransition(beforeDocument, afterDocument) {
  validateRecursiveBounds(beforeDocument);
  validateRecursiveBounds(afterDocument);
  const beforeIsArray = Array.isArray(beforeDocument);
  const afterIsArray = Array.isArray(afterDocument);
  if (beforeIsArray !== afterIsArray) throw new HttpError(400, "bentuk document tidak boleh berubah");
  if (!beforeIsArray) {
    if (!beforeDocument || !afterDocument || !Array.isArray(beforeDocument.brands) || !Array.isArray(afterDocument.brands)) {
      throw new HttpError(400, "dokumen model invalid");
    }
    const beforeBrands = beforeDocument.brands.map(function (row) { return row && row.brand; });
    const afterBrands = new Set(afterDocument.brands.map(function (row) { return row && row.brand; }));
    const missingBrand = beforeBrands.find(function (brand) { return !afterBrands.has(brand); });
    if (missingBrand) throw new HttpError(400, "core brand hilang: " + missingBrand);
    if (!sameJson(envelopeMetadata(beforeDocument), envelopeMetadata(afterDocument))) {
      throw new HttpError(400, "brand/envelope legacy metadata wajib dipertahankan");
    }
  }

  const beforeRows = transitionRows(beforeDocument);
  const afterRows = transitionRows(afterDocument);
  if (!afterRows.length) throw new HttpError(400, "empty payload / dokumen kosong ditolak");
  const beforeMap = new Map(beforeRows.map(function (row) { return [row.id, row]; }));
  const afterMap = new Map(afterRows.map(function (row) { return [row.id, row]; }));
  const removed = beforeRows.filter(function (row) { return !afterMap.has(row.id); });
  const added = afterRows.filter(function (row) { return !beforeMap.has(row.id); });
  const edited = beforeRows.filter(function (row) {
    return afterMap.has(row.id) && !sameJson(row.model, afterMap.get(row.id).model);
  });
  const isRename = removed.length === 1 && added.length === 1 && removed[0].brand === added[0].brand;
  const actualRemovalCount = isRename ? 0 : removed.length;
  if (actualRemovalCount > 0 && beforeRows.length > 0 && actualRemovalCount * 2 >= beforeRows.length) {
    throw new HttpError(400, "50%/mass removal ditolak");
  }

  let operation;
  let operationCount;
  if (isRename) {
    operation = { type: "rename", before: removed[0], after: added[0] };
    operationCount = 1 + edited.length;
  } else {
    operationCount = removed.length + added.length + edited.length;
    if (removed.length === 1 && !added.length && !edited.length) {
      operation = { type: "delete", before: removed[0] };
    } else if (added.length === 1 && !removed.length && !edited.length) {
      operation = { type: "add", after: added[0] };
    } else if (edited.length === 1 && !removed.length && !added.length) {
      operation = { type: "edit", before: edited[0], after: afterMap.get(edited[0].id) };
    }
  }
  if (operationCount !== 1 || !operation) {
    throw new HttpError(400, "PUT wajib tepat satu model add/delete/rename/edit");
  }
  if (!expectedOrder(beforeRows, afterRows, operation)) {
    throw new HttpError(400, "urutan model/legacy metadata berubah di luar operasi UI");
  }
  validateGroupTransition(beforeDocument, afterDocument, operation);
  return {
    type: operation.type,
    before_id: operation.before ? operation.before.id : null,
    after_id: operation.after ? operation.after.id : null,
  };
}

function exactModelId(brand, model) {
  return String(brand || "") + "::" + String(model.model || "");
}

function findModel(document, modelId) {
  const wanted = cleanText(modelId, "model_id", 200);
  if (!wanted.includes("::")) throw new HttpError(400, "model_id wajib exact brand::model");
  const matches = modelRows(document).filter(function (row) {
    return (row.model.model_id || exactModelId(row.brand, row.model)) === wanted;
  });
  if (!matches.length) throw new HttpError(404, "model tidak ditemukan");
  if (matches.length !== 1) throw new HttpError(409, "model_id duplikat");
  return matches[0].model;
}

function normalizeFeatures(value) {
  if (!Array.isArray(value)) throw new HttpError(400, "fitur wajib array");
  if (value.length > 100) throw new HttpError(400, "fitur terlalu banyak");
  return value.map(function (item) {
    return cleanText(item, "fitur", 500);
  });
}

function normalizeFeatureInput(value) {
  return value == null ? [] : normalizeFeatures(value);
}

function defaultFeatureMeta(features) {
  return {
    source_url: null,
    source_kind: null,
    verified_at: null,
    origin: features.length ? "legacy" : "unknown",
    user_locked: false,
  };
}

function ensureFeatureState(model) {
  model.fitur = normalizeFeatureInput(model.fitur);
  if (!model.fitur_meta || typeof model.fitur_meta !== "object" || Array.isArray(model.fitur_meta)) {
    model.fitur_meta = defaultFeatureMeta(model.fitur);
  }
  if (!Array.isArray(model.feature_suggestions)) model.feature_suggestions = [];
}

function setUserFeatures(model, value, suppliedMeta) {
  ensureFeatureState(model);
  const previous = model.fitur_meta;
  const payload = suppliedMeta && typeof suppliedMeta === "object" && !Array.isArray(suppliedMeta) ? suppliedMeta : {};
  const provenance = validateProvenance({
    source_url: own(payload, "source_url") ? payload.source_url : previous.source_url,
    source_kind: own(payload, "source_kind") ? payload.source_kind : previous.source_kind,
    verified_at: own(payload, "verified_at") ? payload.verified_at : previous.verified_at,
  }, false);
  model.fitur = normalizeFeatureInput(value);
  model.fitur_meta = {
    source_url: provenance.source_url,
    source_kind: provenance.source_kind,
    verified_at: provenance.verified_at,
    origin: "user",
    user_locked: true,
  };
}

function ensureKnownKey(key, knownKeys) {
  const cleanKey = cleanText(key, "key", 64);
  if (!knownKeys.has(cleanKey)) throw new HttpError(400, "kategori yatim: " + cleanKey);
  return cleanKey;
}

function setUserValue(model, key, raw, knownKeys) {
  key = ensureKnownKey(key, knownKeys);
  if (!model.spec_values || typeof model.spec_values !== "object" || Array.isArray(model.spec_values)) {
    model.spec_values = {};
  }
  const previous = model.spec_values[key] && typeof model.spec_values[key] === "object" ? model.spec_values[key] : {};
  const payload = raw && typeof raw === "object" && !Array.isArray(raw) && own(raw, "value") ? raw : { value: raw };
  const provenance = validateProvenance({
    source_url: own(payload, "source_url") ? payload.source_url : previous.source_url,
    source_kind: own(payload, "source_kind") ? payload.source_kind : previous.source_kind,
    verified_at: own(payload, "verified_at") ? payload.verified_at : previous.verified_at,
  }, false);
  model.spec_values[key] = {
    value: normalizeScalar(payload.value),
    source_url: provenance.source_url,
    source_kind: provenance.source_kind,
    verified_at: provenance.verified_at,
    origin: "user",
    user_locked: true,
  };
}

function suggestionFingerprint(item) {
  return JSON.stringify([
    item.key,
    item.value,
    item.source_url || null,
    item.source_kind || null,
    item.verified_at || null,
    item.status || "pending",
  ]);
}

function suggestionAt(model, index) {
  if (!Array.isArray(model.research_suggestions)) model.research_suggestions = [];
  if (!Number.isInteger(index) || index < 0 || index >= model.research_suggestions.length) {
    throw new HttpError(404, "suggestion tidak ditemukan");
  }
  const suggestion = model.research_suggestions[index];
  if (!suggestion || typeof suggestion !== "object") throw new HttpError(400, "suggestion invalid");
  if ((suggestion.status || "pending") !== "pending") throw new HttpError(409, "suggestion sudah diputuskan");
  return suggestion;
}

function featureSuggestionFingerprint(item) {
  return JSON.stringify([
    item.fitur,
    item.source_url || null,
    item.source_kind || null,
    item.verified_at || null,
    item.status || "pending",
  ]);
}

function featureSuggestionAt(model, index) {
  if (!Array.isArray(model.feature_suggestions)) model.feature_suggestions = [];
  if (!Number.isInteger(index) || index < 0 || index >= model.feature_suggestions.length) {
    throw new HttpError(404, "feature suggestion tidak ditemukan");
  }
  const suggestion = model.feature_suggestions[index];
  if (!suggestion || typeof suggestion !== "object") throw new HttpError(400, "feature suggestion invalid");
  if ((suggestion.status || "pending") !== "pending") throw new HttpError(409, "feature suggestion sudah diputuskan");
  return suggestion;
}

function validateFeatureState(model) {
  if (!Array.isArray(model.fitur)) throw new HttpError(400, "fitur wajib array utama");
  normalizeFeatures(model.fitur);
  const meta = model.fitur_meta;
  if (!meta || typeof meta !== "object" || Array.isArray(meta)) throw new HttpError(400, "fitur_meta wajib object");
  if (!new Set(["unknown", "legacy", "research", "user"]).has(meta.origin)) {
    throw new HttpError(400, "fitur_meta origin invalid");
  }
  if (typeof meta.user_locked !== "boolean") throw new HttpError(400, "fitur_meta user_locked wajib boolean");
  validateProvenance(meta, meta.origin === "research");
  if (meta.origin === "unknown" && model.fitur.length) throw new HttpError(400, "fitur unknown wajib kosong");
  if (meta.origin === "user" && meta.user_locked !== true) {
    throw new HttpError(400, "fitur edit user wajib user_locked=true");
  }

  if (!Array.isArray(model.feature_suggestions)) throw new HttpError(400, "feature_suggestions wajib array");
  model.feature_suggestions.forEach(function (suggestion) {
    if (!suggestion || typeof suggestion !== "object" || Array.isArray(suggestion)) {
      throw new HttpError(400, "feature suggestion invalid");
    }
    normalizeFeatures(suggestion.fitur);
    validateProvenance(suggestion, true);
    if (suggestion.origin !== "research") throw new HttpError(400, "feature suggestion origin wajib research");
    if (!["pending", "accepted", "rejected"].includes(suggestion.status || "pending")) {
      throw new HttpError(400, "status feature suggestion invalid");
    }
  });
}

function validateModelDynamicState(model, knownKeys) {
  if (!model.spec_values || typeof model.spec_values !== "object" || Array.isArray(model.spec_values)) {
    throw new HttpError(400, "spec_values harus object");
  }
  Object.keys(model.spec_values).forEach(function (key) {
    if (!knownKeys.has(key)) throw new HttpError(400, "kategori yatim: " + key);
    const entry = model.spec_values[key];
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) throw new HttpError(400, "spec value invalid");
    normalizeScalar(entry.value);
    validateProvenance(entry, entry.origin === "research" && entry.value !== null);
    if (!new Set(["unknown", "legacy", "research", "user"]).has(entry.origin)) {
      throw new HttpError(400, "origin invalid");
    }
    if (typeof entry.user_locked !== "boolean") throw new HttpError(400, "user_locked wajib boolean");
  });
  if (!Array.isArray(model.research_suggestions)) throw new HttpError(400, "research_suggestions harus array");
  model.research_suggestions.forEach(function (suggestion) {
    if (!suggestion || typeof suggestion !== "object") throw new HttpError(400, "suggestion invalid");
    ensureKnownKey(suggestion.key, knownKeys);
    normalizeScalar(suggestion.value);
    validateProvenance(suggestion, false);
    if (!["pending", "accepted", "rejected"].includes(suggestion.status || "pending")) {
      throw new HttpError(400, "status suggestion invalid");
    }
  });
  validateFeatureState(model);
}

export function prepareModelDocument(document, categoryDocument, requireDynamic) {
  validateCategoryDocument(categoryDocument);
  const result = clone(document);
  const knownKeys = new Set(categoryItems(categoryDocument).map(function (item) { return item.key; }));
  const seen = new Set();
  modelRows(result).forEach(function (row) {
    if (typeof row.brand !== "string" || !row.brand.trim()) throw new HttpError(400, "brand wajib diisi");
    if (!row.model || typeof row.model.model !== "string" || !row.model.model.trim()) {
      throw new HttpError(400, "model wajib diisi");
    }
    const expectedId = exactModelId(row.brand, row.model);
    if (seen.has(expectedId)) throw new HttpError(409, "model_id duplikat: " + expectedId);
    seen.add(expectedId);
    validateStoredUrlState(row.model);
    const hasDynamic = own(row.model, "model_id") || own(row.model, "spec_values") || own(row.model, "research_suggestions") ||
      own(row.model, "fitur_meta") || own(row.model, "feature_suggestions");
    if (requireDynamic || hasDynamic) {
      if (row.model.model_id && row.model.model_id !== expectedId) {
        throw new HttpError(400, "model_id wajib exact brand::model");
      }
      row.model.model_id = expectedId;
      if (row.model.spec_values == null) row.model.spec_values = {};
      if (row.model.research_suggestions == null) row.model.research_suggestions = [];
      ensureFeatureState(row.model);
      validateModelDynamicState(row.model, knownKeys);
    } else if (own(row.model, "fitur")) {
      row.model.fitur = normalizeFeatureInput(row.model.fitur);
    }
  });
  return result;
}

export function mutateModelDocument(document, operation, categoryDocument, now) {
  if (!operation || typeof operation !== "object" || !ALLOWED_ACTIONS.has(operation.action)) {
    throw new HttpError(400, "invalid input/action model");
  }
  validateCategoryDocument(categoryDocument);
  const knownKeys = new Set(categoryItems(categoryDocument).map(function (item) { return item.key; }));
  const result = clone(document);
  const model = findModel(result, operation.model_id);
  if (!model.spec_values || typeof model.spec_values !== "object" || Array.isArray(model.spec_values)) model.spec_values = {};
  if (!Array.isArray(model.research_suggestions)) model.research_suggestions = [];
  ensureFeatureState(model);
  const decidedAt = typeof now === "string" ? now : new Date().toISOString();

  if (operation.action === "set_spec_value") {
    setUserValue(model, operation.key, operation.entry || { value: operation.value }, knownKeys);
  } else if (operation.action === "set_features") {
    if (!own(operation, "fitur")) throw new HttpError(400, "fitur wajib ada");
    setUserFeatures(model, operation.fitur, operation.fitur_meta);
  } else if (operation.action === "update_model") {
    if (own(operation, "fitur")) setUserFeatures(model, operation.fitur, operation.fitur_meta);
    if (own(operation, "spec_values")) {
      if (!operation.spec_values || typeof operation.spec_values !== "object" || Array.isArray(operation.spec_values)) {
        throw new HttpError(400, "spec_values patch harus object");
      }
      Object.keys(operation.spec_values).forEach(function (key) {
        setUserValue(model, key, operation.spec_values[key], knownKeys);
      });
    }
    if (!own(operation, "fitur") && !own(operation, "spec_values")) {
      throw new HttpError(400, "update_model tidak berisi perubahan");
    }
  } else if (operation.action === "submit_research") {
    const key = ensureKnownKey(operation.key, knownKeys);
    const candidate = operation.entry;
    if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
      throw new HttpError(400, "entry research wajib object");
    }
    const provenance = validateProvenance(candidate, true);
    const researchEntry = {
      value: normalizeScalar(candidate.value),
      source_url: provenance.source_url,
      source_kind: provenance.source_kind,
      verified_at: provenance.verified_at,
      origin: "research",
      user_locked: false,
    };
    if (researchEntry.value === null) throw new HttpError(400, "nilai research tidak boleh kosong");
    const existing = model.spec_values[key];
    const protectedValue = existing && (existing.origin === "user" || existing.user_locked === true);
    if (!existing || (existing.value === null && !protectedValue)) {
      model.spec_values[key] = researchEntry;
    } else if (existing.value !== researchEntry.value) {
      const suggestion = {
        key,
        value: researchEntry.value,
        source_url: researchEntry.source_url,
        source_kind: researchEntry.source_kind,
        verified_at: researchEntry.verified_at,
        origin: "research",
        status: "pending",
      };
      const fingerprint = suggestionFingerprint(suggestion);
      const duplicate = model.research_suggestions.some(function (item) {
        return suggestionFingerprint(item) === fingerprint;
      });
      if (!duplicate) model.research_suggestions.push(suggestion);
    }
  } else if (operation.action === "accept_suggestion") {
    const suggestion = suggestionAt(model, operation.suggestion_index);
    const key = ensureKnownKey(suggestion.key, knownKeys);
    const provenance = validateProvenance(suggestion, false);
    model.spec_values[key] = {
      value: normalizeScalar(suggestion.value),
      source_url: provenance.source_url,
      source_kind: provenance.source_kind,
      verified_at: provenance.verified_at,
      origin: "user",
      user_locked: true,
    };
    suggestion.status = "accepted";
    suggestion.decided_at = decidedAt;
  } else if (operation.action === "reject_suggestion") {
    const suggestion = suggestionAt(model, operation.suggestion_index);
    suggestion.status = "rejected";
    suggestion.decided_at = decidedAt;
  } else if (operation.action === "submit_research_features") {
    const candidate = operation.entry && typeof operation.entry === "object" ? operation.entry : operation;
    if (!own(candidate, "fitur")) throw new HttpError(400, "fitur research wajib ada");
    const provenance = validateProvenance(candidate, true);
    const researchedFeatures = normalizeFeatures(candidate.fitur);
    const protectedFeatures = model.fitur_meta.origin === "user" || model.fitur_meta.user_locked === true;
    const different = JSON.stringify(model.fitur) !== JSON.stringify(researchedFeatures);
    if (protectedFeatures && different) {
      const featureSuggestion = {
        fitur: researchedFeatures,
        source_url: provenance.source_url,
        source_kind: provenance.source_kind,
        verified_at: provenance.verified_at,
        origin: "research",
        status: "pending",
      };
      const fingerprint = featureSuggestionFingerprint(featureSuggestion);
      const duplicate = model.feature_suggestions.some(function (item) {
        return featureSuggestionFingerprint(item) === fingerprint;
      });
      if (!duplicate) model.feature_suggestions.push(featureSuggestion);
    } else if (!protectedFeatures) {
      model.fitur = researchedFeatures;
      model.fitur_meta = {
        source_url: provenance.source_url,
        source_kind: provenance.source_kind,
        verified_at: provenance.verified_at,
        origin: "research",
        user_locked: false,
      };
    }
  } else if (operation.action === "accept_feature_suggestion") {
    const suggestion = featureSuggestionAt(model, operation.suggestion_index);
    const provenance = validateProvenance(suggestion, true);
    model.fitur = normalizeFeatures(suggestion.fitur);
    model.fitur_meta = {
      source_url: provenance.source_url,
      source_kind: provenance.source_kind,
      verified_at: provenance.verified_at,
      origin: "user",
      user_locked: true,
    };
    suggestion.status = "accepted";
    suggestion.decided_at = decidedAt;
  } else if (operation.action === "reject_feature_suggestion") {
    const suggestion = featureSuggestionAt(model, operation.suggestion_index);
    suggestion.status = "rejected";
    suggestion.decided_at = decidedAt;
  }

  validateStoredUrlState(model);
  validateModelDynamicState(model, knownKeys);
  return { data: result, model: clone(model) };
}

function utf8ToBase64(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (let index = 0; index < bytes.length; index += 1) binary += String.fromCharCode(bytes[index]);
  return btoa(binary);
}

function base64ToUtf8(value) {
  const binary = atob(String(value).replace(/\s/g, ""));
  const bytes = Uint8Array.from(binary, function (character) { return character.charCodeAt(0); });
  return new TextDecoder().decode(bytes);
}

function githubUrl(path, branch) {
  const encodedPath = String(path).split("/").map(encodeURIComponent).join("/");
  return "https://api.github.com/repos/Louisfernaldi/mtms-aqua-haier-kb-data/contents/" +
    encodedPath + "?ref=" + encodeURIComponent(branch || "main");
}

function githubHeaders(env) {
  return {
    Authorization: "Bearer " + env.GITHUB_TOKEN,
    Accept: "application/vnd.github+json",
    "User-Agent": "mtms-aqua-haier-kb",
    "Content-Type": "application/json",
  };
}

export async function readGithubJson(env, path, fetchImpl = fetch) {
  const branch = env.DATA_BRANCH || "main";
  const response = await fetchImpl(githubUrl(path, branch), {
    method: "GET",
    headers: githubHeaders(env),
  });
  if (!response.ok) throw new HttpError(502, "GH_READ_" + response.status);
  const metadata = await response.json();
  if (!metadata || typeof metadata.sha !== "string" || typeof metadata.content !== "string") {
    throw new HttpError(502, "GH_READ_INVALID");
  }
  try {
    return { data: JSON.parse(base64ToUtf8(metadata.content)), sha: metadata.sha, branch };
  } catch (_error) {
    throw new HttpError(502, "GH_JSON_INVALID");
  }
}

export async function writeGithubJson(env, path, data, baseSha, message, fetchImpl = fetch) {
  if (!baseSha) throw new HttpError(428, "base SHA / If-Match wajib");
  validateRecursiveBounds(data);
  const branch = env.DATA_BRANCH || "main";
  const url = githubUrl(path, branch).replace(/\?ref=.*$/, "");
  const response = await fetchImpl(url, {
    method: "PUT",
    headers: githubHeaders(env),
    body: JSON.stringify({
      message,
      content: utf8ToBase64(JSON.stringify(data, null, 2) + "\n"),
      sha: baseSha,
      branch,
    }),
  });
  if (response.status === 409 || response.status === 422) {
    throw new HttpError(412, "stale SHA: data berubah, muat ulang sebelum menyimpan");
  }
  if (!response.ok) throw new HttpError(502, "GH_WRITE_" + response.status);
  const payload = await response.json();
  const sha = payload && payload.content && payload.content.sha;
  if (typeof sha !== "string" || !sha) throw new HttpError(502, "GH_WRITE_INVALID");
  return sha;
}

export function requestBaseSha(request, body) {
  let value = request.headers.get("If-Match") || (body && body.base_sha) || "";
  value = String(value).trim().replace(/^W\//, "").replace(/^"|"$/g, "");
  if (!value) throw new HttpError(428, "base SHA / If-Match wajib");
  if (!/^[a-f0-9]{7,64}$/i.test(value)) throw new HttpError(400, "base SHA invalid");
  return value;
}

export function assertFreshSha(baseSha, currentSha) {
  if (baseSha !== currentSha) throw new HttpError(412, "stale SHA: data berubah, muat ulang sebelum menyimpan");
}

export function etagHeaders(sha) {
  return { ETag: '"' + sha + '"', "X-Data-SHA": sha };
}

export function jsonResponse(payload, status = 200, headers = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...headers,
    },
  });
}

export function errorResponse(error) {
  const status = error instanceof HttpError ? error.status : 500;
  const message = error instanceof HttpError ? error.message : "internal error";
  return jsonResponse({ error: message }, status);
}
