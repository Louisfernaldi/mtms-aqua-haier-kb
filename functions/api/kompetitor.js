// Pages Function: authenticated GET/PUT/PATCH /api/kompetitor.
// Model mutations are atomic, schema-validated, and guarded by an exact base SHA.

import {
  assertFreshSha,
  errorResponse,
  etagHeaders,
  jsonResponse,
  mutateModelDocument,
  prepareModelDocument,
  readJsonBodyCapped,
  readGithubJson,
  requestBaseSha,
  validateDocumentTransition,
  validateRecursiveBounds,
  writeGithubJson,
} from "../_lib/dynamic-specs.js";

const DEFAULT_PATH = "kompetitor.json";
const DEFAULT_CATEGORIES_PATH = "spec-categories.json";

function dataPath(env) {
  return env.KOMPETITOR_PATH || DEFAULT_PATH;
}

function categoriesPath(env) {
  return env.SPEC_CATEGORIES_PATH || DEFAULT_CATEGORIES_PATH;
}

function validEnvelope(value) {
  if (!value || typeof value !== "object" || !Array.isArray(value.brands)) return false;
  const brands = value.brands.map(function (row) { return row && row.brand; });
  return brands.every(function (brand) { return typeof brand === "string" && brand.trim(); }) &&
    brands.length === new Set(brands).size &&
    value.brands.every(function (row) { return Array.isArray(row.models); });
}

export async function onRequestGet(context) {
  try {
    const current = await readGithubJson(context.env, dataPath(context.env));
    if (!validEnvelope(current.data)) throw new Error("kompetitor data invalid");
    return jsonResponse(current.data, 200, {
      ...etagHeaders(current.sha),
      "Cache-Control": "private, max-age=5",
    });
  } catch (error) {
    return errorResponse(error);
  }
}

export async function onRequestPut(context) {
  let body;
  try {
    body = await readJsonBodyCapped(context.request);
    validateRecursiveBounds(body);
  } catch (error) {
    return errorResponse(error);
  }
  const data = body && body.data && validEnvelope(body.data) ? body.data : body;
  if (!validEnvelope(data)) {
    return jsonResponse({ error: "invalid payload: need unique brands with models" }, 400);
  }
  try {
    const baseSha = requestBaseSha(context.request, body);
    const path = dataPath(context.env);
    const current = await readGithubJson(context.env, path);
    assertFreshSha(baseSha, current.sha);
    validateDocumentTransition(current.data, data);
    const categories = await readGithubJson(context.env, categoriesPath(context.env));
    const next = prepareModelDocument(data, categories.data, true);
    const sha = await writeGithubJson(
      context.env,
      path,
      next,
      current.sha,
      "update kompetitor via editor web"
    );
    return jsonResponse({ ok: true, sha }, 200, etagHeaders(sha));
  } catch (error) {
    return errorResponse(error);
  }
}

export async function onRequestPatch(context) {
  let body;
  try {
    body = await readJsonBodyCapped(context.request);
    validateRecursiveBounds(body);
  } catch (error) {
    return errorResponse(error);
  }
  if (!body || typeof body.action !== "string" || typeof body.model_id !== "string") {
    return jsonResponse({ error: "invalid input/action model" }, 400);
  }
  try {
    const baseSha = requestBaseSha(context.request, body);
    const path = dataPath(context.env);
    const current = await readGithubJson(context.env, path);
    assertFreshSha(baseSha, current.sha);
    const categories = await readGithubJson(context.env, categoriesPath(context.env));
    const mutation = mutateModelDocument(current.data, body, categories.data);
    const sha = await writeGithubJson(
      context.env,
      path,
      mutation.data,
      current.sha,
      "ubah spesifikasi model via editor web"
    );
    return jsonResponse({ ok: true, sha, model: mutation.model }, 200, etagHeaders(sha));
  } catch (error) {
    return errorResponse(error);
  }
}
