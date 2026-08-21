// Pages Function: authenticated GET/PATCH /api/spec-categories.
// Authentication is enforced by functions/_middleware.js for every /api/* path.

import {
  assertFreshSha,
  errorResponse,
  etagHeaders,
  jsonResponse,
  mutateCategories,
  readJsonBodyCapped,
  readGithubJson,
  requestBaseSha,
  validateCategoryDocument,
  validateRecursiveBounds,
  writeGithubJson,
} from "../_lib/dynamic-specs.js";

const DEFAULT_PATH = "spec-categories.json";

function dataPath(env) {
  return env.SPEC_CATEGORIES_PATH || DEFAULT_PATH;
}

export async function onRequestGet(context) {
  try {
    const current = await readGithubJson(context.env, dataPath(context.env));
    validateCategoryDocument(current.data);
    return jsonResponse(current.data, 200, {
      ...etagHeaders(current.sha),
      "Cache-Control": "private, max-age=5",
    });
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
  try {
    const baseSha = requestBaseSha(context.request, body);
    const path = dataPath(context.env);
    const current = await readGithubJson(context.env, path);
    assertFreshSha(baseSha, current.sha);
    const next = mutateCategories(current.data, body);
    const sha = await writeGithubJson(
      context.env,
      path,
      next,
      current.sha,
      body.action === "create_category" ? "tambah kategori spesifikasi via editor web" : "ubah kategori spesifikasi via editor web"
    );
    return jsonResponse({ ok: true, sha, spec_categories: next.spec_categories }, 200, etagHeaders(sha));
  } catch (error) {
    return errorResponse(error);
  }
}
