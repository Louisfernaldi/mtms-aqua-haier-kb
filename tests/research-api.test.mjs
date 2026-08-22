import test from "node:test";
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";

if (!globalThis.crypto) globalThis.crypto = webcrypto;

import { authHash } from "../functions/_lib/config.js";
import {
  normalizeCandidate,
  suggestionIdFor,
} from "../functions/_lib/research-jobs.js";
import {
  onRequestGet,
  onRequestPatch,
  onRequestPost,
} from "../functions/api/research.js";

const CORE_KEYS = [
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

const categories = {
  spec_categories: CORE_KEYS.map((key, index) => ({
    key,
    label: key,
    group: "Core",
    unit: null,
    comparison: true,
    order: (index + 1) * 10,
    active: true,
  })),
};

function modelFixture(overrides = {}) {
  return {
    model: "MODEL-1",
    model_id: "AQUA::MODEL-1",
    source_url: "https://aquaelektronik.com/product/model-1",
    photo_url: "https://aquaelektronik.com/images/model-1.png",
    spec_values: {
      width_mm: {
        value: 600,
        source_url: null,
        source_kind: null,
        verified_at: null,
        origin: "legacy",
        user_locked: false,
      },
    },
    research_suggestions: [],
    fitur: [],
    fitur_meta: {
      source_url: null,
      source_kind: null,
      verified_at: null,
      origin: "unknown",
      user_locked: false,
    },
    feature_suggestions: [],
    ...overrides,
  };
}

function competitorDocument(model = modelFixture()) {
  return { brands: [{ brand: "AQUA", models: [model] }], groups: [] };
}

function emptyQueue() {
  return { schema_version: 1, jobs: {} };
}

function jobFixture(candidate, id = "1".repeat(32)) {
  return {
    job_id: id,
    model_id: "AQUA::MODEL-1",
    target: "kompetitor",
    status: "queued",
    sources: [{ url: "https://aquaelektronik.com/product/model-1", source_kind: "model_page" }],
    source_state: "ready",
    attempts: 0,
    max_attempts: 2,
    requested_at: "2026-08-22T01:00:00.000Z",
    started_at: null,
    finished_at: null,
    updated_at: "2026-08-22T01:00:00.000Z",
    candidates: candidate ? [candidate] : [],
    error_code: null,
    dispatch: {
      status: "pending",
      attempts: 0,
      max_attempts: 2,
      last_attempt_at: null,
      last_success_at: null,
      error_code: null,
    },
  };
}

function encodeJson(value) {
  return Buffer.from(JSON.stringify(value), "utf8").toString("base64");
}

function decodeJson(value) {
  return JSON.parse(Buffer.from(value, "base64").toString("utf8"));
}

function clone(value) {
  return structuredClone(value);
}

function makeGithubMock(options = {}) {
  const state = {
    queue: clone(options.queue || emptyQueue()),
    queueSha: "a".repeat(40),
    kompetitor: clone(options.kompetitor || competitorDocument()),
    kompetitorSha: "b".repeat(40),
    produk: clone(options.produk || []),
    produkSha: "c".repeat(40),
    categories: clone(options.categories || categories),
    categoriesSha: "d".repeat(40),
    queueCasFailures: options.queueCasFailures || 0,
    targetCasFailures: options.targetCasFailures || 0,
    queueGetStatus: options.queueGetStatus || 200,
  };
  const calls = [];
  let sequence = 0;

  function metadata(data, sha) {
    return new Response(JSON.stringify({ content: encodeJson(data), sha }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }

  function writtenSha(prefix) {
    sequence += 1;
    return prefix.repeat(39) + String(sequence % 10);
  }

  const mock = async function (url, fetchOptions = {}) {
    const method = fetchOptions.method || "GET";
    const call = { url: String(url), method, options: fetchOptions };
    calls.push(call);

    if (call.url.includes("/actions/workflows/research-specs.yml/dispatches")) {
      if (options.workflowThrows) throw new Error("raw workflow failure must stay private");
      return new Response("", { status: options.workflowStatus || 204 });
    }

    if (method === "GET" && call.url.includes("/contents/site-config.json")) {
      return metadata({ login_password: "local-password" }, "9".repeat(40));
    }

    const isQueue = call.url.includes("/contents/research-jobs.json");
    const isKompetitor = call.url.includes("/contents/kompetitor.json");
    const isProduk = call.url.includes("/contents/produk-katalog.json");
    const isCategories = call.url.includes("/contents/spec-categories.json");

    if (method === "GET" && isQueue) {
      if (state.queueGetStatus === 404) return new Response("", { status: 404 });
      return metadata(state.queue, state.queueSha);
    }
    if (method === "GET" && isKompetitor) return metadata(state.kompetitor, state.kompetitorSha);
    if (method === "GET" && isProduk) return metadata(state.produk, state.produkSha);
    if (method === "GET" && isCategories) return metadata(state.categories, state.categoriesSha);

    if (method === "PUT" && isQueue) {
      if (state.queueCasFailures > 0) {
        state.queueCasFailures -= 1;
        return new Response("", { status: 409 });
      }
      const body = JSON.parse(fetchOptions.body);
      const hasSha = Object.prototype.hasOwnProperty.call(body, "sha");
      if (hasSha && body.sha !== state.queueSha) return new Response("", { status: 409 });
      if (state.queueSha === null && hasSha) return new Response("", { status: 409 });
      if (body.branch !== "research-queue") return new Response("", { status: 409 });
      state.queue = decodeJson(body.content);
      state.queueSha = writtenSha("e");
      return new Response(JSON.stringify({ content: { sha: state.queueSha } }), { status: 200 });
    }

    if (method === "PUT" && (isKompetitor || isProduk)) {
      if (state.targetCasFailures > 0) {
        state.targetCasFailures -= 1;
        return new Response("", { status: 409 });
      }
      const body = JSON.parse(fetchOptions.body);
      const currentSha = isKompetitor ? state.kompetitorSha : state.produkSha;
      if (body.sha !== currentSha || body.branch !== "main") return new Response("", { status: 409 });
      const next = decodeJson(body.content);
      const nextSha = writtenSha("f");
      if (isKompetitor) {
        state.kompetitor = next;
        state.kompetitorSha = nextSha;
      } else {
        state.produk = next;
        state.produkSha = nextSha;
      }
      return new Response(JSON.stringify({ content: { sha: nextSha } }), { status: 200 });
    }

    throw new Error("unexpected external fetch: " + method + " " + call.url);
  };
  return { mock, calls, state };
}

async function withMock(mockState, run) {
  const original = globalThis.fetch;
  globalThis.fetch = mockState.mock;
  try {
    return await run(mockState);
  } finally {
    globalThis.fetch = original;
  }
}

function env(overrides = {}) {
  return {
    LOGIN_PASSWORD: "local-password",
    GITHUB_TOKEN: "fake-data-token",
    DATA_BRANCH: "main",
    ...overrides,
  };
}

async function cookieFor(currentEnv) {
  return "mtms_auth=" + await authHash(currentEnv.LOGIN_PASSWORD, currentEnv);
}

async function request(method, path, currentEnv, body, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.auth !== false) headers.set("Cookie", await cookieFor(currentEnv));
  if (method === "POST" || method === "PATCH") {
    headers.set("Origin", options.origin || "https://local.test");
    headers.set("Content-Type", "application/json");
  }
  return new Request("https://local.test" + path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

async function candidateFixture(overrides = {}) {
  return {
    key: "width_mm",
    value: 610,
    observed_value: 600,
    source_url: "https://aquaelektronik.com/product/model-1",
    source_kind: "official_product_page",
    verified_at: "2026-08-22T08:00:00+07:00",
    status: "pending",
    ...overrides,
  };
}

test("direct endpoint unauthorized returns 401 with zero fetch", async () => {
  const currentEnv = env();
  let fetches = 0;
  const original = globalThis.fetch;
  globalThis.fetch = async () => { fetches += 1; throw new Error("unauthorized must stop"); };
  try {
    const response = await onRequestGet({
      request: await request("GET", "/api/research?job_id=" + "1".repeat(32), currentEnv, undefined, { auth: false }),
      env: currentEnv,
    });
    assert.equal(response.status, 401);
    assert.equal(fetches, 0);
  } finally {
    globalThis.fetch = original;
  }
});

test("cross-origin mutation returns 403 before any data fetch", async () => {
  const currentEnv = env();
  const calls = [];
  const original = globalThis.fetch;
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    if (String(url).includes("/contents/site-config.json")) {
      return new Response(JSON.stringify({
        content: encodeJson({ login_password: "local-password" }),
        sha: "9".repeat(40),
      }), { status: 200 });
    }
    throw new Error("cross-origin must stop before data fetch");
  };
  try {
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }, {
        origin: "https://evil.test",
      }),
      env: currentEnv,
    });
    assert.equal(response.status, 403);
    assert.equal(calls.some((url) => /kompetitor|produk-katalog|research-jobs/.test(url)), false);
  } finally {
    globalThis.fetch = original;
  }
});

test("oversized and unknown fields stop before fetch", async () => {
  const currentEnv = env();
  for (const body of [
    { model_id: "AQUA::MODEL-1", url: "https://evil.test" },
    { model_id: "AQUA::" + "x".repeat(1100) },
  ]) {
    let fetches = 0;
    const original = globalThis.fetch;
    globalThis.fetch = async () => { fetches += 1; throw new Error("invalid body must stop"); };
    try {
      const response = await onRequestPost({
        request: await request("POST", "/api/research", currentEnv, body),
        env: currentEnv,
      });
      assert.ok([400, 413].includes(response.status));
      assert.equal(fetches, 0);
    } finally {
      globalThis.fetch = original;
    }
  }
});

test("unknown model returns 404 and never creates queue state", async () => {
  const mockState = makeGithubMock();
  await withMock(mockState, async ({ calls }) => {
    const currentEnv = env();
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "LG::UNKNOWN" }),
      env: currentEnv,
    });
    assert.equal(response.status, 404);
    assert.equal(calls.filter((call) => call.method === "PUT").length, 0);
  });
});

test("durable POST returns under one second only after queue write", async () => {
  const mockState = makeGithubMock();
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env();
    const started = performance.now();
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
    });
    const elapsed = performance.now() - started;
    assert.equal(response.status, 202);
    const payload = await response.json();
    assert.equal(payload.status, "queued");
    assert.equal(typeof payload.poll_after_ms, "number");
    assert.equal(payload.poll_after_ms > 0, true);
    assert.ok(elapsed < 1000, "local mocked POST took " + elapsed + "ms");
    assert.ok(state.queue.jobs[payload.job_id]);
    assert.equal(calls.filter((call) => call.method === "PUT" && call.url.includes("research-jobs.json")).length, 1);
  });
});

test("double click returns one opaque job and performs one queue write", async () => {
  const mockState = makeGithubMock();
  await withMock(mockState, async ({ calls }) => {
    const currentEnv = env();
    const first = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
    });
    const second = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
    });
    const firstBody = await first.json();
    const secondBody = await second.json();
    assert.match(firstBody.job_id, /^[a-f0-9]{32}$/);
    assert.equal(firstBody.job_id, secondBody.job_id);
    assert.equal(firstBody.status, "queued");
    assert.equal(secondBody.status, "queued");
    assert.equal(typeof firstBody.poll_after_ms, "number");
    assert.equal(firstBody.poll_after_ms, 15000);
    assert.equal(calls.filter((call) => call.method === "PUT" && call.url.includes("research-jobs.json")).length, 1);
  });
});

test("opaque GET exposes sanitized status but forbids model enumeration and raw fields", async () => {
  const rawCandidate = await candidateFixture({ value: "<b>610 mm</b>" });
  const job = jobFixture(rawCandidate);
  const queue = emptyQueue();
  queue.jobs[job.job_id] = job;
  const mockState = makeGithubMock({ queue });
  await withMock(mockState, async () => {
    const currentEnv = env();
    const denied = await onRequestGet({
      request: await request("GET", "/api/research?model_id=AQUA%3A%3AMODEL-1", currentEnv),
      env: currentEnv,
    });
    assert.equal(denied.status, 400);
    const response = await onRequestGet({
      request: await request("GET", "/api/research?job_id=" + job.job_id, currentEnv),
      env: currentEnv,
    });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
    const payload = await response.json();
    assert.equal(payload.job_id, job.job_id);
    assert.equal(payload.candidates[0].value, "610 mm");
    assert.equal(JSON.stringify(payload).includes("<b>"), false);
    assert.equal(own(payload, "sources"), false);
    assert.equal(own(payload, "dispatch"), false);
    assert.equal(own(payload, "sha"), false);
  });
});

test("public job payload exposes requested/started/finished timeline fields only", async () => {
  const rawCandidate = await candidateFixture({ value: "610" });
  const job = jobFixture(rawCandidate);
  const queue = emptyQueue();
  queue.jobs[job.job_id] = job;
  const mockState = makeGithubMock({ queue });
  await withMock(mockState, async () => {
    const currentEnv = env();
    const response = await onRequestGet({
      request: await request("GET", "/api/research?job_id=" + job.job_id, currentEnv),
      env: currentEnv,
    });
    const payload = await response.json();
    assert.equal(payload.requested_at, job.requested_at);
    assert.equal(payload.started_at, job.started_at);
    assert.equal(payload.finished_at, job.finished_at);
    assert.equal(own(payload, "created_at"), false);
    assert.equal(own(payload, "updated_at"), false);
  });
});

test("accept conflict preserves newer user edit and performs zero writes", async () => {
  const rawCandidate = await candidateFixture();
  const normalized = await normalizeCandidate(rawCandidate, "AQUA::MODEL-1");
  const job = jobFixture(rawCandidate);
  const queue = emptyQueue();
  queue.jobs[job.job_id] = job;
  const newer = modelFixture({
    spec_values: {
      width_mm: {
        value: 601,
        source_url: null,
        source_kind: null,
        verified_at: null,
        origin: "user",
        user_locked: true,
      },
    },
  });
  const mockState = makeGithubMock({ queue, kompetitor: competitorDocument(newer) });
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env();
    const response = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, {
        action: "accept",
        job_id: job.job_id,
        suggestion_id: normalized.suggestion_id,
      }, { headers: { "If-Match": mockState.state.kompetitorSha } }),
      env: currentEnv,
    });
    assert.equal(response.status, 409);
    assert.equal(calls.filter((call) => call.method === "PUT").length, 0);
    assert.equal(state.kompetitor.brands[0].models[0].spec_values.width_mm.value, 601);
  });
});

test("accept applies full provenance as user lock and is idempotent", async () => {
  const rawCandidate = await candidateFixture();
  const normalized = await normalizeCandidate(rawCandidate, "AQUA::MODEL-1");
  const job = jobFixture(rawCandidate);
  const queue = emptyQueue();
  queue.jobs[job.job_id] = job;
  const mockState = makeGithubMock({ queue });
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env();
    const body = { action: "accept", job_id: job.job_id, suggestion_id: normalized.suggestion_id };
    const first = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, body, {
        headers: { "If-Match": mockState.state.kompetitorSha },
      }),
      env: currentEnv,
    });
    assert.equal(first.status, 200);
    const entry = state.kompetitor.brands[0].models[0].spec_values.width_mm;
    assert.deepEqual(entry, {
      value: 610,
      source_url: rawCandidate.source_url,
      source_kind: rawCandidate.source_kind,
      verified_at: rawCandidate.verified_at,
      origin: "user",
      user_locked: true,
    });
    assert.equal(state.queue.jobs[job.job_id].candidates[0].status, "accepted");
    const targetWrites = calls.filter((call) => call.method === "PUT" && call.url.includes("kompetitor.json")).length;
    const second = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, body, {
        headers: { "If-Match": mockState.state.kompetitorSha },
      }),
      env: currentEnv,
    });
    assert.equal(second.status, 200);
    assert.equal(calls.filter((call) => call.method === "PUT" && call.url.includes("kompetitor.json")).length, targetWrites);
  });
});

test("reject is queue-only and idempotent", async () => {
  const rawCandidate = await candidateFixture();
  const normalized = await normalizeCandidate(rawCandidate, "AQUA::MODEL-1");
  const job = jobFixture(rawCandidate);
  const queue = emptyQueue();
  queue.jobs[job.job_id] = job;
  const mockState = makeGithubMock({ queue });
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env();
    const body = { action: "reject", job_id: job.job_id, suggestion_id: normalized.suggestion_id };
    const first = await onRequestPatch({ request: await request("PATCH", "/api/research", currentEnv, body), env: currentEnv });
    const second = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, body, {
        headers: { "If-Match": mockState.state.kompetitorSha },
      }),
      env: currentEnv,
    });
    assert.equal(first.status, 200);
    assert.equal(second.status, 200);
    assert.equal(state.queue.jobs[job.job_id].candidates[0].status, "rejected");
    assert.equal(calls.filter((call) => call.method === "PUT" && call.url.includes("research-jobs.json")).length, 1);
    assert.equal(calls.filter((call) => call.method === "PUT" && call.url.includes("kompetitor.json")).length, 0);
  });
});

test("dispatch failure leaves durable job queued and hides raw GitHub errors", async () => {
  const mockState = makeGithubMock({ workflowStatus: 500 });
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env({ RESEARCH_WORKFLOW_TOKEN: "separate-workflow-token" });
    const pending = [];
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
      waitUntil(promise) { pending.push(promise); },
    });
    assert.equal(response.status, 202);
    const payload = await response.json();
    await Promise.all(pending);
    const durable = state.queue.jobs[payload.job_id];
    assert.equal(durable.status, "queued");
    assert.equal(durable.dispatch.status, "failed");
    assert.equal(durable.dispatch.error_code, "DISPATCH_HTTP_500");
    assert.equal(JSON.stringify(durable).includes("separate-workflow-token"), false);
    assert.equal(calls.filter((call) => call.url.includes("/actions/workflows/")).length, 1);
  });
});

test("cross-origin PATCH accept returns 403 before any mutation and with no fetch", async () => {
  const rawCandidate = await candidateFixture();
  const normalized = await normalizeCandidate(rawCandidate, "AQUA::MODEL-1");
  const job = jobFixture(rawCandidate);
  const queue = emptyQueue();
  queue.jobs[job.job_id] = job;
  const mockState = makeGithubMock({ queue });
  await withMock(mockState, async ({ calls }) => {
    const currentEnv = env();
    const response = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, {
        action: "accept",
        job_id: job.job_id,
        suggestion_id: normalized.suggestion_id,
      }, {
        origin: "https://evil.test",
        headers: { "If-Match": "b".repeat(40) },
      }),
      env: currentEnv,
    });
    assert.equal(response.status, 403);
    assert.equal(calls.length, 0);
  });
});

test("enqueue writes sources with model-page source kind", async () => {
  const mockState = makeGithubMock({
    kompetitor: competitorDocument(modelFixture({
      source_url: "https://aquaelektronik.com/product/model-1",
      photo_url: "https://aquaelektronik.com.evil/photo/model-1.png",
      spec_values: {
        width_mm: {
          value: 600,
          source_url: "https://evil.aquaelektronik.com/spec-width",
          source_kind: "official_product_page",
          verified_at: "2026-08-22T08:00:00+07:00",
          origin: "research",
          user_locked: false,
        },
      },
    })),
  });
  await withMock(mockState, async ({ state }) => {
    const currentEnv = env();
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
    });
    assert.equal(response.status, 202);
    const payload = await response.json();
    assert.deepEqual(state.queue.jobs[payload.job_id].sources, [{
      url: "https://aquaelektronik.com/product/model-1",
      source_kind: "model_page",
    }]);
  });
});

test("missing research queue document is created with no sha in PUT body", async () => {
  const mockState = makeGithubMock({ queueGetStatus: 404 });
  await withMock(mockState, async ({ calls }) => {
    const currentEnv = env();
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
    });
    assert.equal(response.status, 202);
    const payload = await response.json();
    const queueWrite = calls.find((call) => call.method === "PUT" && call.url.includes("research-jobs.json"));
    assert.ok(queueWrite);
    const body = JSON.parse(queueWrite.options.body);
    assert.ok(!("sha" in body));
    assert.equal(body.branch, "research-queue");
  });
});

test("PATCH accept requires and validates If-Match", async () => {
  const rawCandidate = await candidateFixture();
  const normalized = await normalizeCandidate(rawCandidate, "AQUA::MODEL-1");
  const job = jobFixture(rawCandidate);
  const queue = emptyQueue();
  queue.jobs[job.job_id] = job;
  const mockState = makeGithubMock({ queue });
  await withMock(mockState, async ({}) => {
    const currentEnv = env();
    const body = { action: "accept", job_id: job.job_id, suggestion_id: normalized.suggestion_id };
    const missing = await onRequestPatch({ request: await request("PATCH", "/api/research", currentEnv, body), env: currentEnv });
    const badFormat = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, body, { headers: { "If-Match": "not-a-sha" } }),
      env: currentEnv,
    });
    const wrongSha = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, body, { headers: { "If-Match": "a".repeat(40) } }),
      env: currentEnv,
    });
    const ok = await onRequestPatch({
      request: await request("PATCH", "/api/research", currentEnv, body, {
        headers: { "If-Match": mockState.state.kompetitorSha },
      }),
      env: currentEnv,
    });
    assert.equal(missing.status, 428);
    assert.equal(badFormat.status, 400);
    assert.equal(wrongSha.status, 412);
    assert.equal(ok.status, 200);
  });
});

test("dispatch attempt is capped by max_attempts while POST can be called repeatedly", async () => {
  const mockState = makeGithubMock({ workflowStatus: 500 });
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env({ RESEARCH_WORKFLOW_TOKEN: "separate-workflow-token" });
    const runPost = async () => {
      const pending = [];
      const response = await onRequestPost({
        request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
        env: currentEnv,
        waitUntil(promise) { pending.push(promise); },
      });
      await Promise.all(pending);
      const payload = await response.json();
      return { response, payload };
    };
    const first = await runPost();
    const second = await runPost();
    const third = await runPost();
    assert.equal(first.response.status, 202);
    assert.equal(second.response.status, 202);
    assert.equal(third.response.status, 202);
    assert.equal(first.payload.job_id, second.payload.job_id);
    assert.equal(first.payload.job_id, third.payload.job_id);
    const payloads = [first.payload, second.payload, third.payload];
    assert.equal(payloads.every((payload) => payload.job_id === payloads[0].job_id), true);
    const durable = state.queue.jobs[payloads[0].job_id];
    assert.equal(durable.status, "queued");
    assert.equal(durable.dispatch.attempts, 2);
    assert.equal(durable.dispatch.max_attempts, 2);
    assert.equal(calls.filter((call) => call.url.includes("/actions/workflows/")).length, 2);
  });
});

test("stored URL injection is rejected without arbitrary source fetch", async () => {
  const injected = modelFixture({
    source_url: "https://aquaelektronik.com.evil.test/steal",
    photo_url: "https://user@aquaelektronik.com/private",
    spec_values: {
      width_mm: {
        value: 600,
        source_url: "//aquaelektronik.com/protocol-relative",
        source_kind: "official_product_page",
        verified_at: "2026-08-22T08:00:00+07:00",
        origin: "research",
        user_locked: false,
      },
    },
  });
  const mockState = makeGithubMock({ kompetitor: competitorDocument(injected) });
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env();
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
    });
    assert.equal(response.status, 202);
    const payload = await response.json();
    assert.deepEqual(state.queue.jobs[payload.job_id].sources, []);
    assert.equal(state.queue.jobs[payload.job_id].source_state, "unresolved_ready");
    assert.equal(calls.some((call) => call.url.includes("evil.test") || call.url.includes("/private")), false);
  });
});

test("suggestion hash ignores timestamp, status, and observed_value", async () => {
  const first = await candidateFixture();
  const second = await candidateFixture({
    observed_value: 601,
    verified_at: "2026-08-22T09:30:00+07:00",
    status: "accepted",
  });
  assert.equal(await suggestionIdFor("AQUA::MODEL-1", first), await suggestionIdFor("AQUA::MODEL-1", second));
});

test("queue CAS retry cap is initial attempt plus at most two recomputations", async () => {
  const mockState = makeGithubMock({ queueCasFailures: 10 });
  await withMock(mockState, async ({ calls }) => {
    const currentEnv = env();
    const response = await onRequestPost({
      request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
      env: currentEnv,
    });
    assert.equal(response.status, 409);
    assert.equal(calls.filter((call) => call.method === "PUT" && call.url.includes("research-jobs.json")).length, 3);
  });
});

function workerReceiptJob(overrides = {}) {
  const job = jobFixture(null, "2".repeat(32));
  job.status = "running";
  job.attempts = 1;
  job.started_at = "2026-08-22T09:47:04Z";
  job.error_code = "LAST_FETCH_FAILED";
  job.sources = [{
    url: "https://aquaelektronik.com/product/model-1",
    outcome: "http_error",
    http_status: 403,
    checked_at: "2026-08-22T09:47:05Z",
  }];
  job.dispatch = {
    status: "sent",
    attempts: 1,
    max_attempts: 2,
    last_attempt_at: "2026-08-22T09:46:45.542Z",
    last_success_at: "2026-08-22T09:46:48.033Z",
    error_code: null,
  };
  return Object.assign(job, overrides);
}

test("worker receipt without source_kind stays readable; hostile host receipt is rejected", async () => {
  const healthy = emptyQueue();
  const goodJob = workerReceiptJob();
  healthy.jobs[goodJob.job_id] = goodJob;
  const okState = makeGithubMock({ queue: healthy });
  await withMock(okState, async () => {
    const currentEnv = env();
    const response = await onRequestGet({
      request: await request("GET", "/api/research?job_id=" + goodJob.job_id, currentEnv),
      env: currentEnv,
    });
    assert.equal(response.status, 200);
    const payload = await response.json();
    assert.equal(payload.status, "running");
    assert.equal(payload.error_code, "LAST_FETCH_FAILED");
  });

  const hostile = emptyQueue();
  const badJob = workerReceiptJob({
    sources: [{
      url: "https://evil.example/product/model-1",
      outcome: "http_error",
      http_status: 200,
      checked_at: "2026-08-22T09:47:05Z",
    }],
  });
  hostile.jobs[badJob.job_id] = badJob;
  const badState = makeGithubMock({ queue: hostile });
  await withMock(badState, async () => {
    const currentEnv = env();
    const response = await onRequestGet({
      request: await request("GET", "/api/research?job_id=" + badJob.job_id, currentEnv),
      env: currentEnv,
    });
    assert.equal(response.status, 502);
    const payload = await response.json();
    assert.equal(payload.error, "RESEARCH_QUEUE_INVALID");
  });
});

test("running job stuck on failed fetch is redispatched once per repeat POST", async () => {
  const queue = emptyQueue();
  const stuck = workerReceiptJob({
    dispatch: {
      status: "failed",
      attempts: 1,
      max_attempts: 2,
      last_attempt_at: "2026-08-22T09:46:45.542Z",
      last_success_at: null,
      error_code: "DISPATCH_HTTP_500",
    },
  });
  queue.jobs[stuck.job_id] = stuck;
  const mockState = makeGithubMock({ queue });
  await withMock(mockState, async ({ calls, state }) => {
    const currentEnv = env({ RESEARCH_WORKFLOW_TOKEN: "fake-workflow-token" });
    const runPost = async () => {
      const pending = [];
      const response = await onRequestPost({
        request: await request("POST", "/api/research", currentEnv, { model_id: "AQUA::MODEL-1" }),
        env: currentEnv,
        waitUntil(promise) { pending.push(promise); },
      });
      await Promise.all(pending);
      return response;
    };
    const first = await runPost();
    assert.equal(first.status, 202);
    const body = await first.json();
    assert.equal(body.job_id, stuck.job_id);
    const dispatches = calls.filter(
      (call) => call.method === "POST" && call.url.includes("/actions/workflows/research-specs.yml/dispatches"));
    assert.equal(dispatches.length, 1);
    assert.equal(state.queue.jobs[stuck.job_id].dispatch.attempts, 2);
    const second = await runPost();
    assert.equal(second.status, 202);
    assert.equal(calls.filter(
      (call) => call.method === "POST" && call.url.includes("/actions/workflows/research-specs.yml/dispatches")).length, 1,
      "attempts sudah mencapai max_attempts; tidak boleh dispatch lagi");
  });
});

function own(value, key) {
  return Object.prototype.hasOwnProperty.call(value, key);
}
