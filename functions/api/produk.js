// Pages Function: authenticated GET/PUT/PATCH /api/produk.
// GET keeps the historical array response; ETag/X-Data-SHA carry concurrency state.

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

const DEFAULT_PATH = "produk-katalog.json";
const DEFAULT_CATEGORIES_PATH = "spec-categories.json";

function dataPath(env) {
  return env.DATA_PATH || DEFAULT_PATH;
}

function categoriesPath(env) {
  return env.SPEC_CATEGORIES_PATH || DEFAULT_CATEGORIES_PATH;
}

function validProductArray(value) {
  if (!Array.isArray(value) || !value.every(function (item) {
    return item && typeof item === "object" && typeof item.model === "string" && item.model.trim();
  })) return false;
  const ids = value.map(function (item) { return (item.brand || "AQUA") + "::" + item.model; });
  return ids.length === new Set(ids).size;
}

export async function onRequestGet(context) {
  try {
    const current = await readGithubJson(context.env, dataPath(context.env));
    if (!validProductArray(current.data)) throw new Error("produk data invalid");
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
  const data = body && !Array.isArray(body) && Array.isArray(body.data) ? body.data : body;
  if (!validProductArray(data)) {
    return jsonResponse({ error: "invalid payload: harus array produk unik dengan field model" }, 400);
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
      "update produk via editor web"
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
    const products = await readGithubJson(context.env, dataPath(context.env));
    assertFreshSha(baseSha, products.sha);
    const categories = await readGithubJson(context.env, categoriesPath(context.env));
    const mutation = mutateModelDocument(products.data, body, categories.data);
    const sha = await writeGithubJson(
      context.env,
      dataPath(context.env),
      mutation.data,
      products.sha,
      "ubah spesifikasi produk via editor web"
    );
    return jsonResponse({ ok: true, sha, model: mutation.model }, 200, etagHeaders(sha));
  } catch (error) {
    return errorResponse(error);
  }
}
