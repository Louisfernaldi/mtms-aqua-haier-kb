// Authenticated durable research queue API: POST/GET/PATCH /api/research.
// The endpoint never fetches model source URLs; it only talks to GitHub APIs.

import { authHash, getLoginPassword } from "../_lib/config.js";
import {
  HttpError,
  jsonResponse,
  mutateModelDocument,
  readGithubJson,
  readJsonBodyCapped,
  writeGithubJson,
} from "../_lib/dynamic-specs.js";
import {
  MAX_CAS_RECOMPUTATIONS,
  MAX_DISPATCH_ATTEMPTS,
  casUpdateResearchQueue,
  currentObservedValue,
  deriveOfficialSources,
  findActiveJob,
  findModel,
  isExactModelId,
  isOpaqueJobId,
  locateCandidate,
  newQueuedJob,
  normalizeCandidate,
  observedValueFingerprint,
  publicJob,
  readResearchQueue,
  sanitizeErrorCode,
} from "../_lib/research-jobs.js";

const BODY_LIMIT = 1024;
const DEFAULT_KOMPETITOR_PATH = "kompetitor.json";
const DEFAULT_PRODUK_PATH = "produk-katalog.json";
const DEFAULT_CATEGORIES_PATH = "spec-categories.json";
const WORKFLOW_REPO = "Louisfernaldi/mtms-aqua-haier-kb";
const WORKFLOW_FILE = "research-specs.yml";
const DISPATCH_STALE_MS = 5 * 60 * 1000;
const POLL_AFTER_MS = 15000;

function own(value, key) {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function exactOwnKeys(value, keys) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const expected = keys.slice().sort();
  return actual.length === expected.length && actual.every(function (key, index) { return key === expected[index]; });
}

function cookieHash(request) {
  const header = request.headers.get("Cookie") || "";
  const matches = [];
  header.split(";").forEach(function (part) {
    const separator = part.indexOf("=");
    if (separator < 0 || part.slice(0, separator).trim() !== "mtms_auth") return;
    matches.push(part.slice(separator + 1).trim());
  });
  return matches.length === 1 ? matches[0] : "";
}

function parseIfMatchHeader(request) {
  let value = request.headers.get("If-Match");
  if (!value) throw new HttpError(428, "base SHA / If-Match wajib");
  value = String(value).trim().replace(/^W\//, "").replace(/^"|"$/g, "");
  if (!value) throw new HttpError(428, "base SHA / If-Match wajib");
  if (!/^[a-f0-9]{7,64}$/i.test(value)) throw new HttpError(400, "base SHA invalid");
  return value;
}

function constantTimeHashEqual(left, right) {
  if (typeof left !== "string" || typeof right !== "string" || left.length !== 64 || right.length !== 64) return false;
  let difference = 0;
  for (let index = 0; index < 64; index += 1) difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  return difference === 0;
}

async function authenticated(request, env) {
  const supplied = cookieHash(request);
  if (!/^[a-f0-9]{64}$/.test(supplied)) return false;
  // The shared config resolver prefers the current data-repo password and owns
  // its documented LOGIN_PASSWORD fallback/cache behavior.
  const password = await getLoginPassword(env);
  if (typeof password !== "string" || !password) return false;
  const expected = await authHash(password, env);
  return constantTimeHashEqual(supplied, expected);
}

function originAllowed(request) {
  const supplied = request.headers.get("Origin");
  return typeof supplied === "string" && supplied === new URL(request.url).origin;
}

function safeResponse(error) {
  if (error instanceof HttpError) return jsonResponse({ error: error.message }, error.status);
  return jsonResponse({ error: "internal error" }, 500);
}

async function requireAuth(context) {
  try {
    return await authenticated(context.request, context.env);
  } catch (_error) {
    return false;
  }
}

function dataPath(env, target) {
  if (target === "produk") return env.DATA_PATH || DEFAULT_PRODUK_PATH;
  return env.KOMPETITOR_PATH || DEFAULT_KOMPETITOR_PATH;
}

function categoriesPath(env) {
  return env.SPEC_CATEGORIES_PATH || DEFAULT_CATEGORIES_PATH;
}

async function locateCurrentTarget(env, modelId) {
  const kompetitor = await readGithubJson(env, dataPath(env, "kompetitor"));
  const competitorModel = findModel(kompetitor.data, modelId, "kompetitor");
  if (competitorModel) return { target: "kompetitor", model: competitorModel, current: kompetitor };
  const produk = await readGithubJson(env, dataPath(env, "produk"));
  const productModel = findModel(produk.data, modelId, "produk");
  if (productModel) return { target: "produk", model: productModel, current: produk };
  throw new HttpError(404, "model tidak ditemukan");
}

function dispatchIsEligible(job, nowMs) {
  const active = job && (job.status === "queued" || job.status === "running");
  if (!active) return false;
  const dispatch = job.dispatch && typeof job.dispatch === "object" ? job.dispatch : {};
  const attempts = Number.isInteger(dispatch.attempts) ? dispatch.attempts : 0;
  if (attempts >= MAX_DISPATCH_ATTEMPTS) return false;
  if (attempts === 0 || dispatch.status === "failed") return true;
  const lastAttempt = Date.parse(dispatch.last_attempt_at || "");
  return (dispatch.status === "pending" || dispatch.status === "dispatching" ||
      dispatch.status === "sent") &&
    (!Number.isFinite(lastAttempt) || nowMs - lastAttempt >= DISPATCH_STALE_MS);
}

async function reserveDispatch(env, jobId) {
  return casUpdateResearchQueue(env, async function (queue) {
    const job = queue.jobs[jobId];
    const now = new Date().toISOString();
    if (!dispatchIsEligible(job, Date.parse(now))) return { changed: false, result: null };
    const previous = job.dispatch && typeof job.dispatch === "object" ? job.dispatch : {};
    job.dispatch = {
      status: "dispatching",
      attempts: (Number.isInteger(previous.attempts) ? previous.attempts : 0) + 1,
      max_attempts: MAX_DISPATCH_ATTEMPTS,
      last_attempt_at: now,
      last_success_at: previous.last_success_at || null,
      error_code: null,
    };
    job.updated_at = now;
    return {
      changed: true,
      message: "reserve research workflow dispatch",
      result: { job_id: job.job_id, model_id: job.model_id, attempt: job.dispatch.attempts },
    };
  });
}

async function finishDispatch(env, reservation, ok, errorCode) {
  if (!reservation) return;
  await casUpdateResearchQueue(env, async function (queue) {
    const job = queue.jobs[reservation.job_id];
    if (!job || !job.dispatch || job.dispatch.attempts !== reservation.attempt ||
        job.dispatch.status !== "dispatching") return { changed: false, result: null };
    const now = new Date().toISOString();
    job.dispatch.status = ok ? "sent" : "failed";
    job.dispatch.last_success_at = ok ? now : (job.dispatch.last_success_at || null);
    job.dispatch.error_code = ok ? null : sanitizeErrorCode(errorCode || "DISPATCH_FAILED");
    job.updated_at = now;
    return { changed: true, message: "record research workflow dispatch", result: null };
  });
}

async function dispatchDurableJob(env, jobId) {
  let reservation;
  try {
    reservation = await reserveDispatch(env, jobId);
    if (!reservation) return;
    if (!env.RESEARCH_WORKFLOW_TOKEN) {
      await finishDispatch(env, reservation, false, "DISPATCH_NOT_CONFIGURED");
      return;
    }
    const url = "https://api.github.com/repos/" + WORKFLOW_REPO + "/actions/workflows/" +
      encodeURIComponent(WORKFLOW_FILE) + "/dispatches";
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + env.RESEARCH_WORKFLOW_TOKEN,
        Accept: "application/vnd.github+json",
        "User-Agent": "mtms-aqua-haier-kb",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ref: env.RESEARCH_WORKFLOW_REF || "main",
        inputs: { job_id: reservation.job_id, model_id: reservation.model_id },
      }),
    });
    await finishDispatch(env, reservation, response.ok, response.ok ? null : "DISPATCH_HTTP_" + response.status);
  } catch (_error) {
    try {
      await finishDispatch(env, reservation, false, "DISPATCH_FAILED");
    } catch (_ignored) {
      // The durable queued job remains the source of truth even if failure recording loses a CAS race.
    }
  }
}

function scheduleDispatch(context, job) {
  if (!job || typeof context.waitUntil !== "function") return;
  const task = dispatchDurableJob(context.env, job.job_id);
  try {
    context.waitUntil(task);
  } catch (_error) {
    task.catch(function () {});
  }
}

function scalarEqual(left, right) {
  return typeof left === typeof right && Object.is(left, right);
}

function candidateAlreadyApplied(model, candidate) {
  const entry = model && model.spec_values && model.spec_values[candidate.key];
  return Boolean(entry && typeof entry === "object" && scalarEqual(entry.value, candidate.value) &&
    entry.source_url === candidate.source_url && entry.source_kind === candidate.source_kind &&
    entry.verified_at === candidate.verified_at && entry.origin === "user" && entry.user_locked === true);
}

async function verifyObservedValue(model, candidate) {
  const currentFingerprint = await observedValueFingerprint(currentObservedValue(model, candidate.key));
  const expectedFingerprint = await observedValueFingerprint(candidate.observed_value);
  if (currentFingerprint !== expectedFingerprint) throw new HttpError(409, "nilai saat ini sudah berubah");
}

async function claimAcceptDecision(env, initial, jobId, suggestionId) {
  return casUpdateResearchQueue(env, async function (queue) {
    const job = queue.jobs[jobId];
    if (!job) throw new HttpError(404, "job tidak ditemukan");
    const located = await locateCandidate(job, suggestionId);
    if (located.candidate.status === "accepted") return { changed: false, result: { job, already: true } };
    if (located.candidate.status === "rejected") throw new HttpError(409, "suggestion sudah ditolak");
    if (located.raw.decision_state === "accepting") return { changed: false, result: { job, already: false } };
    located.raw.decision_state = "accepting";
    located.raw.decision_started_at = new Date().toISOString();
    job.updated_at = located.raw.decision_started_at;
    return { changed: true, message: "claim research suggestion accept", result: { job, already: false } };
  }, { initial });
}

async function releaseAcceptDecision(env, jobId, suggestionId) {
  try {
    await casUpdateResearchQueue(env, async function (queue) {
      const job = queue.jobs[jobId];
      if (!job) return { changed: false, result: null };
      const located = await locateCandidate(job, suggestionId);
      if (located.candidate.status !== "pending" || located.raw.decision_state !== "accepting") {
        return { changed: false, result: null };
      }
      delete located.raw.decision_state;
      delete located.raw.decision_started_at;
      job.updated_at = new Date().toISOString();
      return { changed: true, message: "release research suggestion accept", result: null };
    });
  } catch (_error) {
    // A retry can safely reconcile an accepting candidate against the current target value.
  }
}

async function writeAcceptedValue(env, job, candidate, initialTarget, initialCategories) {
  let target = initialTarget;
  let categories = initialCategories;
  let recomputations = 0;
  while (true) {
    const model = findModel(target.data, job.model_id, job.target);
    if (!model) throw new HttpError(409, "model target sudah berubah");
    if (candidateAlreadyApplied(model, candidate)) return;
    await verifyObservedValue(model, candidate);
    const mutation = mutateModelDocument(target.data, {
      action: "set_spec_value",
      model_id: job.model_id,
      key: candidate.key,
      entry: {
        value: candidate.value,
        source_url: candidate.source_url,
        source_kind: candidate.source_kind,
        verified_at: candidate.verified_at,
      },
    }, categories.data);
    try {
      await writeGithubJson(
        env,
        dataPath(env, job.target),
        mutation.data,
        target.sha,
        "accept durable research suggestion"
      );
      return;
    } catch (error) {
      if (!(error instanceof HttpError) || error.status !== 412 || recomputations >= MAX_CAS_RECOMPUTATIONS) {
        if (error instanceof HttpError && error.status === 412) throw new HttpError(409, "target data sibuk");
        throw error;
      }
      recomputations += 1;
      target = await readGithubJson(env, dataPath(env, job.target));
      categories = await readGithubJson(env, categoriesPath(env));
    }
  }
}

async function markCandidateAccepted(env, jobId, suggestionId) {
  return casUpdateResearchQueue(env, async function (queue) {
    const job = queue.jobs[jobId];
    if (!job) throw new HttpError(404, "job tidak ditemukan");
    const located = await locateCandidate(job, suggestionId);
    if (located.candidate.status === "accepted") return { changed: false, result: job };
    if (located.candidate.status === "rejected") throw new HttpError(409, "suggestion sudah ditolak");
    located.raw.status = "accepted";
    located.raw.decided_at = new Date().toISOString();
    delete located.raw.decision_state;
    delete located.raw.decision_started_at;
    job.updated_at = located.raw.decided_at;
    return { changed: true, message: "accept durable research suggestion", result: job };
  });
}

async function rejectCandidate(env, initial, jobId, suggestionId) {
  return casUpdateResearchQueue(env, async function (queue) {
    const job = queue.jobs[jobId];
    if (!job) throw new HttpError(404, "job tidak ditemukan");
    const located = await locateCandidate(job, suggestionId);
    if (located.candidate.status === "rejected") return { changed: false, result: job };
    if (located.candidate.status === "accepted") throw new HttpError(409, "suggestion sudah diterima");
    if (located.raw.decision_state === "accepting") throw new HttpError(409, "suggestion sedang diterima");
    located.raw.status = "rejected";
    located.raw.decided_at = new Date().toISOString();
    job.updated_at = located.raw.decided_at;
    return { changed: true, message: "reject durable research suggestion", result: job };
  }, { initial });
}

export async function onRequestPost(context) {
  if (!(await requireAuth(context))) return jsonResponse({ error: "unauthorized" }, 401);
  if (!originAllowed(context.request)) return jsonResponse({ error: "cross-origin mutation forbidden" }, 403);
  let body;
  try {
    body = await readJsonBodyCapped(context.request, BODY_LIMIT);
    if (!exactOwnKeys(body, ["model_id"]) || !isExactModelId(body.model_id)) {
      throw new HttpError(400, "invalid input: exact model_id only");
    }
    const located = await locateCurrentTarget(context.env, body.model_id);
    const brand = body.model_id.split("::", 1)[0];
    const sources = deriveOfficialSources(located.model, brand);
    const initialQueue = await readResearchQueue(context.env);
    let proposed = null;
    const result = await casUpdateResearchQueue(context.env, async function (queue) {
      const existing = findActiveJob(queue, body.model_id);
      if (existing) return { changed: false, result: { job: existing, created: false } };
      if (!proposed || queue.jobs[proposed.job_id]) {
        proposed = newQueuedJob(body.model_id, located.target, sources, new Date().toISOString(), queue);
      }
      queue.jobs[proposed.job_id] = proposed;
      return {
        changed: true,
        message: "queue one model research job",
        result: { job: proposed, created: true },
      };
    }, { initial: initialQueue });
    scheduleDispatch(context, result.job);
    return jsonResponse({ job_id: result.job.job_id, status: "queued", poll_after_ms: POLL_AFTER_MS }, 202);
  } catch (error) {
    return safeResponse(error);
  }
}

export async function onRequestGet(context) {
  if (!(await requireAuth(context))) return jsonResponse({ error: "unauthorized" }, 401);
  try {
    const url = new URL(context.request.url);
    const entries = Array.from(url.searchParams.entries());
    if (entries.length !== 1 || entries[0][0] !== "job_id" || !isOpaqueJobId(entries[0][1])) {
      throw new HttpError(400, "opaque job_id query required");
    }
    const queue = await readResearchQueue(context.env);
    const job = queue.data.jobs[entries[0][1]];
    if (!job) throw new HttpError(404, "job tidak ditemukan");
    return jsonResponse(await publicJob(job), 200, { "Cache-Control": "no-store" });
  } catch (error) {
    return safeResponse(error);
  }
}

export async function onRequestPatch(context) {
  if (!(await requireAuth(context))) return jsonResponse({ error: "unauthorized" }, 401);
  if (!originAllowed(context.request)) return jsonResponse({ error: "cross-origin mutation forbidden" }, 403);
  try {
    const body = await readJsonBodyCapped(context.request, BODY_LIMIT);
    if (!exactOwnKeys(body, ["action", "job_id", "suggestion_id"]) ||
        !["accept", "reject"].includes(body.action) || !isOpaqueJobId(body.job_id) ||
        typeof body.suggestion_id !== "string" || !/^[a-f0-9]{64}$/.test(body.suggestion_id)) {
      throw new HttpError(400, "invalid decision input");
    }
    const initialQueue = await readResearchQueue(context.env);
    const initialJob = initialQueue.data.jobs[body.job_id];
    if (!initialJob) throw new HttpError(404, "job tidak ditemukan");
    const initialCandidate = await locateCandidate(initialJob, body.suggestion_id);

    if (body.action === "reject") {
      const job = await rejectCandidate(context.env, initialQueue, body.job_id, body.suggestion_id);
      return jsonResponse(await publicJob(job), 200);
    }

    const expectedSha = parseIfMatchHeader(context.request);
    const target = await readGithubJson(context.env, dataPath(context.env, initialJob.target));
    const categories = await readGithubJson(context.env, categoriesPath(context.env));
    if (target.sha !== expectedSha) throw new HttpError(412, "base SHA / If-Match tidak cocok");

    if (initialCandidate.candidate.status === "accepted") return jsonResponse(await publicJob(initialJob), 200);
    if (initialCandidate.candidate.status === "rejected") throw new HttpError(409, "suggestion sudah ditolak");
    const model = findModel(target.data, initialJob.model_id, initialJob.target);
    if (!model) throw new HttpError(409, "model target sudah berubah");
    if (!candidateAlreadyApplied(model, initialCandidate.candidate)) {
      await verifyObservedValue(model, initialCandidate.candidate);
    }

    const claim = await claimAcceptDecision(context.env, initialQueue, body.job_id, body.suggestion_id);
    if (claim.already) return jsonResponse(await publicJob(claim.job), 200);
    try {
      await writeAcceptedValue(context.env, initialJob, initialCandidate.candidate, target, categories);
    } catch (error) {
      if (error instanceof HttpError && error.status === 409 && /nilai saat ini/.test(error.message)) {
        await releaseAcceptDecision(context.env, body.job_id, body.suggestion_id);
      }
      throw error;
    }
    const accepted = await markCandidateAccepted(context.env, body.job_id, body.suggestion_id);
    return jsonResponse(await publicJob(accepted), 200);
  } catch (error) {
    return safeResponse(error);
  }
}
