// Durable research queue helpers for Cloudflare Pages Functions.
// Queue state lives only in the data repository and every mutation uses SHA CAS.

import { HttpError } from "./dynamic-specs.js";

export const RESEARCH_DATA_REPO = "Louisfernaldi/mtms-aqua-haier-kb-data";
export const DEFAULT_RESEARCH_BRANCH = "research-queue";
export const DEFAULT_RESEARCH_JOBS_PATH = "research-jobs.json";
export const MAX_CAS_RECOMPUTATIONS = 2;
export const MAX_DISPATCH_ATTEMPTS = 2;

const ACTIVE_STATUSES = new Set(["queued", "running"]);
const JOB_STATUSES = new Set(["queued", "running", "completed", "failed", "unresolved"]);
const CANDIDATE_STATUSES = new Set(["pending", "accepted", "rejected"]);
const OFFICIAL_HOSTS = Object.freeze({
  AQUA: new Set(["aquaelektronik.com"]),
  LG: new Set(["www.lg.com", "lg.com"]),
  MIDEA: new Set(["www.midea.com", "midea.com"]),
  POLYTRON: new Set(["polytron.co.id", "www.polytron.co.id"]),
  SAMSUNG: new Set(["www.samsung.com", "samsung.com"]),
  SHARP: new Set(["id.sharp", "global.sharp"]),
});

function own(value, key) {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
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

function queueBranch(env) {
  return String(env.RESEARCH_BRANCH || DEFAULT_RESEARCH_BRANCH);
}

function queuePath(env) {
  return String(env.RESEARCH_JOBS_PATH || DEFAULT_RESEARCH_JOBS_PATH);
}

function encodedPath(path) {
  return String(path).split("/").map(encodeURIComponent).join("/");
}

function queueUrl(env, includeRef) {
  const base = "https://api.github.com/repos/" + RESEARCH_DATA_REPO + "/contents/" + encodedPath(queuePath(env));
  return includeRef ? base + "?ref=" + encodeURIComponent(queueBranch(env)) : base;
}

function queueHeaders(env) {
  return {
    Authorization: "Bearer " + (env.GITHUB_TOKEN || ""),
    Accept: "application/vnd.github+json",
    "User-Agent": "mtms-aqua-haier-kb",
    "Content-Type": "application/json",
  };
}

function isIpLiteral(hostname) {
  if (/^\d{1,3}(?:\.\d{1,3}){3}$/.test(hostname)) return true;
  return hostname.includes(":") || hostname.startsWith("[") || hostname.endsWith("]");
}

function brandFromModelId(modelId) {
  return typeof modelId === "string" ? modelId.split("::", 1)[0].toUpperCase() : "";
}

const SOURCE_KINDS = Object.freeze(new Set(["model_page", "spec_value", "photo"]));

function cleanText(value, maxLength) {
  if (typeof value !== "string") return "";
  return value
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/<[^>]*>/g, " ")
    .replace(/[<>]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function normalizeScalar(value, allowNull) {
  if (value === null && allowNull) return null;
  if (typeof value === "string") {
    const result = cleanText(value, 1000);
    if (!result && !allowNull) throw new HttpError(400, "candidate value invalid");
    return result || null;
  }
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "boolean") return value;
  throw new HttpError(400, "candidate value invalid");
}

function stableScalar(value) {
  if (value === null) return "null";
  if (typeof value === "string") return "string:" + value;
  if (typeof value === "number") return "number:" + String(value);
  if (typeof value === "boolean") return "boolean:" + String(value);
  return "invalid";
}

async function sha256Hex(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest)).map(function (byte) {
    return byte.toString(16).padStart(2, "0");
  }).join("");
}

export function safeOfficialSourceUrl(value, brand) {
  if (typeof value !== "string" || !value || value.startsWith("//")) return null;
  if (/[\u0000-\u001f\u007f\\]/.test(value)) return null;
  let parsed;
  try {
    parsed = new URL(value);
  } catch (_error) {
    return null;
  }
  const hostname = parsed.hostname.toLowerCase();
  const allowed = OFFICIAL_HOSTS[String(brand || "").toUpperCase()];
  if (!allowed || parsed.protocol !== "https:" || parsed.username || parsed.password || parsed.port) return null;
  if (!hostname || isIpLiteral(hostname) || !allowed.has(hostname)) return null;
  return parsed.href;
}

export function deriveOfficialSources(model, brand) {
  const raw = [];
  if (model && typeof model === "object") {
    if (model.source_url) raw.push({ value: model.source_url, source_kind: "model_page" });
    if (model.spec_values && typeof model.spec_values === "object" && !Array.isArray(model.spec_values)) {
      Object.keys(model.spec_values).sort().forEach(function (key) {
        const entry = model.spec_values[key];
        if (entry && typeof entry === "object") {
          raw.push({ value: entry.source_url, source_kind: "spec_value" });
        }
      });
    }
    raw.push({ value: model.photo_url, source_kind: "photo" });
  }
  const result = [];
  const seen = new Set();
  raw.forEach(function (entry) {
    if (!entry || typeof entry.value !== "string") return;
    const safe = safeOfficialSourceUrl(entry.value, brand);
    if (!safe || seen.has(safe) || result.length >= 2) return;
    seen.add(safe);
    result.push({ url: safe, source_kind: entry.source_kind });
  });
  return result;
}

export function randomJobId() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes).map(function (byte) { return byte.toString(16).padStart(2, "0"); }).join("");
}

export function isOpaqueJobId(value) {
  return typeof value === "string" && /^[a-f0-9]{32,128}$/.test(value);
}

export function sanitizeErrorCode(value) {
  if (value == null || value === "") return null;
  const code = String(value).toUpperCase().replace(/[^A-Z0-9_]/g, "_").slice(0, 64);
  return code || "RESEARCH_ERROR";
}

export function findModel(document, modelId, target) {
  if (!isExactModelId(modelId)) return null;
  if (target === "produk") {
    if (!Array.isArray(document)) return null;
    return document.find(function (model) {
      return model && ((model.brand || "AQUA") + "::" + model.model) === modelId;
    }) || null;
  }
  if (target === "kompetitor") {
    if (!document || !Array.isArray(document.brands)) return null;
    for (const brandRow of document.brands) {
      if (!brandRow || !Array.isArray(brandRow.models)) continue;
      const found = brandRow.models.find(function (model) {
        return model && (brandRow.brand + "::" + model.model) === modelId;
      });
      if (found) return found;
    }
  }
  return null;
}

export function isExactModelId(value) {
  return typeof value === "string" && value.length <= 300 && /^[^:\s][^:]*::[^:\s][^:]*$/.test(value);
}

export function currentObservedValue(model, key) {
  if (!model || !model.spec_values || typeof model.spec_values !== "object") return null;
  const entry = model.spec_values[key];
  if (!entry || typeof entry !== "object" || !own(entry, "value")) return null;
  return normalizeScalar(entry.value, true);
}

export async function observedValueFingerprint(value) {
  return sha256Hex("observed-v1|" + stableScalar(normalizeScalar(value, true)));
}

export async function suggestionIdFor(modelId, candidate) {
  const stable = [
    "suggestion-v2",
    modelId,
    candidate.key,
    stableScalar(candidate.value),
    candidate.source_url || null,
  ];
  return sha256Hex(JSON.stringify(stable));
}

export async function normalizeCandidate(candidate, modelId) {
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
    throw new HttpError(400, "candidate invalid");
  }
  const key = cleanText(candidate.key, 64);
  if (!/^[a-z][a-z0-9_]*$/.test(key)) throw new HttpError(400, "candidate key invalid");
  const value = normalizeScalar(candidate.value, false);
  const observedValue = normalizeScalar(own(candidate, "observed_value") ? candidate.observed_value : null, true);
  const sourceUrl = safeOfficialSourceUrl(candidate.source_url, brandFromModelId(modelId));
  const sourceKind = cleanText(candidate.source_kind, 80);
  const verifiedAt = cleanText(candidate.verified_at, 64);
  if (!sourceUrl || !sourceKind || !verifiedAt || Number.isNaN(Date.parse(verifiedAt)) ||
      !/(?:Z|[+-]\d\d:\d\d)$/.test(verifiedAt)) {
    throw new HttpError(400, "candidate provenance invalid");
  }
  const status = CANDIDATE_STATUSES.has(candidate.status) ? candidate.status : "pending";
  const normalized = {
    key,
    value,
    observed_value: observedValue,
    source_url: sourceUrl,
    source_kind: sourceKind,
    verified_at: verifiedAt,
    status,
  };
  normalized.suggestion_id = await suggestionIdFor(modelId, normalized);
  if (candidate.decided_at && !Number.isNaN(Date.parse(candidate.decided_at))) {
    normalized.decided_at = String(candidate.decided_at);
  }
  return normalized;
}

export async function locateCandidate(job, suggestionId) {
  if (!job || !Array.isArray(job.candidates)) throw new HttpError(404, "suggestion tidak ditemukan");
  for (let index = 0; index < job.candidates.length; index += 1) {
    let normalized;
    try {
      normalized = await normalizeCandidate(job.candidates[index], job.model_id);
    } catch (_error) {
      continue;
    }
    if (normalized.suggestion_id === suggestionId) return { index, raw: job.candidates[index], candidate: normalized };
  }
  throw new HttpError(404, "suggestion tidak ditemukan");
}

export function validateQueueDocument(document) {
  if (!document || typeof document !== "object" || Array.isArray(document) || document.schema_version !== 1 ||
      !document.jobs || typeof document.jobs !== "object" || Array.isArray(document.jobs)) {
    throw new HttpError(502, "RESEARCH_QUEUE_INVALID");
  }
  const ids = Object.keys(document.jobs);
  if (ids.length > 5000) throw new HttpError(502, "RESEARCH_QUEUE_TOO_LARGE");
  ids.forEach(function (id) {
    const job = document.jobs[id];
    if (!isOpaqueJobId(id) || !job || typeof job !== "object" || job.job_id !== id ||
        !isExactModelId(job.model_id) || !["kompetitor", "produk"].includes(job.target) ||
        !JOB_STATUSES.has(job.status) || !Array.isArray(job.sources) || job.sources.length > 2 ||
        typeof job.requested_at !== "string" || !job.requested_at ||
        !(job.started_at === null || typeof job.started_at === "string") ||
        !(job.finished_at === null || typeof job.finished_at === "string") ||
        !Array.isArray(job.candidates) || job.candidates.length > 100 ||
        !job.sources.every(function (source) {
          const safe = safeOfficialSourceUrl(source && source.url, brandFromModelId(job.model_id));
          // Receipt hasil worker boleh menggantikan kind dengan outcome/http_status/checked_at,
          // tapi host URL tetap diwajibkan resmi (anti SSRF) di semua bentuk.
          const receipt = source && typeof source === "object" && !Array.isArray(source) &&
            (typeof source.outcome === "string" || typeof source.http_status === "number");
          return source && typeof source === "object" && !Array.isArray(source) &&
            typeof source.url === "string" && source.url === safe &&
            (receipt || SOURCE_KINDS.has(source.source_kind));
        }) ||
        !Number.isInteger(job.attempts) || job.attempts < 0 || job.attempts > MAX_DISPATCH_ATTEMPTS ||
        job.max_attempts !== MAX_DISPATCH_ATTEMPTS) {
      throw new HttpError(502, "RESEARCH_QUEUE_INVALID");
    }
  });
  return document;
}

export async function readResearchQueue(env, fetchImpl = fetch) {
  const response = await fetchImpl(queueUrl(env, true), { method: "GET", headers: queueHeaders(env) });
  if (response.status === 404) return { data: { schema_version: 1, jobs: {} }, sha: null };
  if (!response.ok) throw new HttpError(502, "RESEARCH_QUEUE_READ_FAILED");
  const metadata = await response.json();
  if (!metadata || typeof metadata.sha !== "string" || typeof metadata.content !== "string") {
    throw new HttpError(502, "RESEARCH_QUEUE_READ_INVALID");
  }
  try {
    const data = JSON.parse(base64ToUtf8(metadata.content));
    validateQueueDocument(data);
    return { data, sha: metadata.sha };
  } catch (error) {
    if (error instanceof HttpError) throw error;
    throw new HttpError(502, "RESEARCH_QUEUE_JSON_INVALID");
  }
}

export async function writeResearchQueue(env, data, baseSha, message, fetchImpl = fetch) {
  validateQueueDocument(data);
  if (baseSha !== null && (typeof baseSha !== "string" || !baseSha)) {
    throw new HttpError(502, "RESEARCH_QUEUE_SHA_REQUIRED");
  }
  const body = {
    message: cleanText(message, 120) || "update durable research queue",
    content: utf8ToBase64(JSON.stringify(data, null, 2) + "\n"),
    branch: queueBranch(env),
  };
  if (baseSha) body.sha = baseSha;
  const response = await fetchImpl(queueUrl(env, false), {
    method: "PUT",
    headers: queueHeaders(env),
    body: JSON.stringify(body),
  });
  if (response.status === 409 || response.status === 422) throw new HttpError(412, "RESEARCH_QUEUE_CAS_STALE");
  if (!response.ok) throw new HttpError(502, "RESEARCH_QUEUE_WRITE_FAILED");
  const payload = await response.json();
  const sha = payload && payload.content && payload.content.sha;
  if (typeof sha !== "string" || !sha) throw new HttpError(502, "RESEARCH_QUEUE_WRITE_INVALID");
  return sha;
}

export async function casUpdateResearchQueue(env, transform, options = {}) {
  let current = options.initial || null;
  let recomputations = 0;
  while (true) {
    if (!current) current = await readResearchQueue(env, options.fetchImpl || fetch);
    const next = clone(current.data);
    const transformed = await transform(next);
    if (!transformed || transformed.changed === false) return transformed ? transformed.result : undefined;
    try {
      const sha = await writeResearchQueue(
        env,
        next,
        current.sha,
        transformed.message || "update durable research queue",
        options.fetchImpl || fetch
      );
      return transformed.result === undefined ? { sha } : transformed.result;
    } catch (error) {
      if (!(error instanceof HttpError) || error.status !== 412 || recomputations >= MAX_CAS_RECOMPUTATIONS) {
        if (error instanceof HttpError && error.status === 412) throw new HttpError(409, "RESEARCH_QUEUE_BUSY");
        throw error;
      }
      recomputations += 1;
      current = null;
    }
  }
}

export function findActiveJob(queue, modelId) {
  return Object.values(queue.jobs).find(function (job) {
    return job && job.model_id === modelId && ACTIVE_STATUSES.has(job.status);
  }) || null;
}

export function newQueuedJob(modelId, target, sources, now, queue) {
  let jobId = randomJobId();
  for (let attempt = 0; attempt < 4 && queue.jobs[jobId]; attempt += 1) jobId = randomJobId();
  if (queue.jobs[jobId]) throw new HttpError(503, "RESEARCH_JOB_ID_UNAVAILABLE");
  return {
    job_id: jobId,
    model_id: modelId,
    target,
    status: "queued",
    sources: sources.slice(0, 2),
    source_state: sources.length ? "ready" : "unresolved_ready",
    attempts: 0,
    max_attempts: MAX_DISPATCH_ATTEMPTS,
    requested_at: now,
    started_at: null,
    finished_at: null,
    updated_at: now,
    candidates: [],
    error_code: null,
    dispatch: {
      status: "pending",
      attempts: 0,
      max_attempts: MAX_DISPATCH_ATTEMPTS,
      last_attempt_at: null,
      last_success_at: null,
      error_code: null,
    },
  };
}

export async function publicJob(job) {
  const candidates = [];
  if (job && Array.isArray(job.candidates)) {
    for (const raw of job.candidates) {
      try {
        const candidate = await normalizeCandidate(raw, job.model_id);
        candidates.push(candidate);
      } catch (_error) {
        // Malformed worker output is omitted instead of being exposed to the UI.
      }
    }
  }
  return {
    job_id: job.job_id,
    model_id: cleanText(job.model_id, 300),
    target: ["kompetitor", "produk"].includes(job.target) ? job.target : null,
    status: JOB_STATUSES.has(job.status) ? job.status : "failed",
    requested_at: cleanText(job.requested_at, 64) || null,
    started_at: job.started_at === null ? null : cleanText(job.started_at, 64),
    finished_at: job.finished_at === null ? null : cleanText(job.finished_at, 64),
    error_code: sanitizeErrorCode(job.error_code),
    candidates,
  };
}
