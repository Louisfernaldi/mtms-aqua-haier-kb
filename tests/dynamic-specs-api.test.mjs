import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

import { onRequest as authMiddleware } from "../functions/_middleware.js";
import {
  HttpError,
  mutateCategories,
  mutateModelDocument,
  readJsonBodyCapped,
  validateDocumentTransition,
  validateRecursiveBounds,
} from "../functions/_lib/dynamic-specs.js";
import { onRequestPatch as patchCategories } from "../functions/api/spec-categories.js";
import {
  onRequestPatch as patchCompetitor,
  onRequestPut as putCompetitor,
} from "../functions/api/kompetitor.js";
import {
  onRequestPatch as patchProduk,
  onRequestPut as putProduk,
} from "../functions/api/produk.js";

const categories = JSON.parse(
  await readFile(new URL("../site/data/spec-categories.json", import.meta.url), "utf8")
);

function modelDocument() {
  return {
    brands: [{
      brand: "AQUA",
      models: [{
        model: "MODEL-1",
        model_id: "AQUA::MODEL-1",
        fitur: ["Bullet lama"],
        spec_values: {},
        research_suggestions: [],
      }],
    }],
  };
}

function produkArray42() {
  return Array.from({ length: 42 }, (_, index) => ({
    brand: "AQUA",
    model: "PRODUK-" + String(index + 1).padStart(2, "0"),
    fitur: [],
  }));
}

function base64Json(value) {
  return Buffer.from(JSON.stringify(value), "utf8").toString("base64");
}

function githubRead(value, sha) {
  return new Response(JSON.stringify({ content: base64Json(value), sha }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function githubWrite(sha) {
  return new Response(JSON.stringify({ content: { sha } }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

async function withMockFetch(mock, callback) {
  const previous = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async function (url, options = {}) {
    const call = { url: String(url), method: options.method || "GET", options };
    calls.push(call);
    return mock(call, calls);
  };
  try {
    return await callback(calls);
  } finally {
    globalThis.fetch = previous;
  }
}

test("unauthorized API request returns 401 before endpoint and performs no live write", async () => {
  await withMockFetch(
    (call) => {
      assert.equal(call.method, "GET");
      return new Response("offline config miss", { status: 503 });
    },
    async (calls) => {
      let nextCalled = false;
      const response = await authMiddleware({
        request: new Request("https://local.test/api/spec-categories"),
        env: { LOGIN_PASSWORD: "offline-only", GITHUB_TOKEN: "fake-token" },
        next() { nextCalled = true; },
      });
      assert.equal(response.status, 401);
      assert.equal(nextCalled, false);
      assert.equal(calls.some((call) => call.method === "PUT"), false);
    }
  );
});

test("invalid input endpoint returns 400 without crossing network boundary", async () => {
  await withMockFetch(
    () => { throw new Error("fetch must not be called for invalid input"); },
    async (calls) => {
      const response = await patchCompetitor({
        request: new Request("https://local.test/api/kompetitor", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify({ action: "invalid" }),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 400);
      assert.equal(calls.length, 0);
    }
  );
});

test("oversized Content-Length returns 413 before any fetch", async () => {
  await withMockFetch(
    () => { throw new Error("oversized Content-Length must perform zero network calls"); },
    async (calls) => {
      const response = await patchCategories({
        request: new Request("https://local.test/api/spec-categories", {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": String(2 * 1024 * 1024 + 1),
            "If-Match": '"aaaaaaaa"',
          },
          body: "{}",
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 413);
      assert.equal(calls.length, 0);
    }
  );
});

test("chunked body without Content-Length returns 413 at the hard cap with zero fetch", async () => {
  const chunk = new Uint8Array(700 * 1024).fill(97);
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(chunk);
      controller.enqueue(chunk);
      controller.enqueue(chunk);
      controller.close();
    },
  });
  await withMockFetch(
    () => { throw new Error("oversized stream must perform zero network calls"); },
    async (calls) => {
      const response = await patchProduk({
        request: new Request("https://local.test/api/produk", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: stream,
          duplex: "half",
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 413);
      assert.equal(calls.length, 0);
    }
  );
});

test("malformed JSON returns 400 before any fetch", async () => {
  await withMockFetch(
    () => { throw new Error("malformed JSON must perform zero network calls"); },
    async (calls) => {
      const response = await patchCompetitor({
        request: new Request("https://local.test/api/kompetitor", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: "{bad",
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 400);
      assert.equal(calls.length, 0);
    }
  );
});

test("oversized PATCH ignored extra field returns 413 before field validation or fetch", async () => {
  const payload = JSON.stringify({ action: "ignored", extra: "x".repeat(2 * 1024 * 1024 + 1) });
  await withMockFetch(
    () => { throw new Error("oversized ignored field must perform zero network calls"); },
    async (calls) => {
      const response = await patchCompetitor({
        request: new Request("https://local.test/api/kompetitor", {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": String(Buffer.byteLength(payload)),
            "If-Match": '"aaaaaaaa"',
          },
          body: payload,
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 413);
      assert.equal(calls.length, 0);
    }
  );
});

test("streaming decoder preserves UTF-8 multibyte characters split across chunks", async () => {
  const expected = { text: "A\u{1F600}B" };
  const utf8 = new TextEncoder().encode(JSON.stringify(expected));
  const emojiStart = utf8.findIndex((byte) => byte === 0xf0);
  assert.notEqual(emojiStart, -1);
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(utf8.slice(0, emojiStart + 2));
      controller.enqueue(utf8.slice(emojiStart + 2));
      controller.close();
    },
  });
  const parsed = await readJsonBodyCapped(new Request("https://local.test/api/body", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: stream,
    duplex: "half",
  }));
  assert.deepEqual(parsed, expected);
});

test("duplicate key kategori is rejected and never reaches GitHub PUT", async () => {
  await withMockFetch(
    (call) => {
      assert.equal(call.method, "GET");
      return githubRead(categories, "aaaaaaaa");
    },
    async (calls) => {
      const duplicate = { ...categories.spec_categories[0], order: 130 };
      const response = await patchCategories({
        request: new Request("https://local.test/api/spec-categories", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify({ action: "create_category", category: duplicate }),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 409);
      assert.match((await response.json()).error, /duplicate|duplikat/i);
      assert.equal(calls.some((call) => call.method === "PUT"), false);
    }
  );
});

test("stale SHA returns 412 and performs zero write", async () => {
  await withMockFetch(
    () => githubRead(categories, "bbbbbbbb"),
    async (calls) => {
      const response = await patchCategories({
        request: new Request("https://local.test/api/spec-categories", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify({
            action: "update_category",
            key: "form_factor",
            patch: { label: "Tipe Kulkas" },
          }),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 412);
      assert.equal(calls.filter((call) => call.method === "PUT").length, 0);
    }
  );
});

test("edit value user always stamps origin=user and user_locked=true", () => {
  const result = mutateModelDocument(modelDocument(), {
    action: "set_spec_value",
    model_id: "AQUA::MODEL-1",
    key: "width_mm",
    value: 600,
  }, categories);
  assert.deepEqual(result.model.spec_values.width_mm, {
    value: 600,
    source_url: null,
    source_kind: null,
    verified_at: null,
    origin: "user",
    user_locked: true,
  });
});

test("user lock blocks research overwrite and creates one pending suggestion", () => {
  const locked = mutateModelDocument(modelDocument(), {
    action: "set_spec_value",
    model_id: "AQUA::MODEL-1",
    key: "width_mm",
    value: 600,
  }, categories).data;
  const researched = mutateModelDocument(locked, {
    action: "submit_research",
    model_id: "AQUA::MODEL-1",
    key: "width_mm",
    entry: {
      value: 610,
      source_url: "https://example.com/model-1",
      source_kind: "brand_official",
      verified_at: "2026-08-21T10:00:00+07:00",
    },
  }, categories);
  assert.equal(researched.model.spec_values.width_mm.value, 600);
  assert.equal(researched.model.spec_values.width_mm.user_locked, true);
  assert.equal(researched.model.research_suggestions.length, 1);
  assert.equal(researched.model.research_suggestions[0].status, "pending");
});

test("protected null stays null for origin=user and user_locked=true when research is non-null", () => {
  const cases = [
    {
      name: "origin=user",
      entry: {
        value: null,
        source_url: null,
        source_kind: null,
        verified_at: null,
        origin: "user",
        user_locked: false,
      },
    },
    {
      name: "user_locked=true",
      entry: {
        value: null,
        source_url: null,
        source_kind: null,
        verified_at: null,
        origin: "legacy",
        user_locked: true,
      },
    },
  ];

  for (const scenario of cases) {
    const source = modelDocument();
    source.brands[0].models[0].spec_values.width_mm = { ...scenario.entry };

    const researched = mutateModelDocument(source, {
      action: "submit_research",
      model_id: "AQUA::MODEL-1",
      key: "width_mm",
      entry: {
        value: 610,
        source_url: "https://example.com/model-1",
        source_kind: "brand_official",
        verified_at: "2026-08-21T10:00:00+07:00",
      },
    }, categories);

    assert.equal(researched.model.spec_values.width_mm.value, null, scenario.name);
    assert.equal(researched.model.spec_values.width_mm.origin, scenario.entry.origin, scenario.name);
    assert.equal(researched.model.spec_values.width_mm.user_locked, scenario.entry.user_locked, scenario.name);
    assert.equal(researched.model.research_suggestions.length, 1, scenario.name);
    assert.equal(researched.model.research_suggestions[0].value, 610, scenario.name);
    assert.equal(researched.model.research_suggestions[0].status, "pending", scenario.name);
  }
});

test("set_features and update_model stamp fitur_meta origin=user and user_locked=true", () => {
  const setResult = mutateModelDocument(modelDocument(), {
    action: "set_features",
    model_id: "AQUA::MODEL-1",
    fitur: ["Bullet user"],
  }, categories);
  assert.deepEqual(setResult.model.fitur, ["Bullet user"]);
  assert.equal(setResult.model.fitur_meta.origin, "user");
  assert.equal(setResult.model.fitur_meta.user_locked, true);

  const updateResult = mutateModelDocument(modelDocument(), {
    action: "update_model",
    model_id: "AQUA::MODEL-1",
    fitur: [],
  }, categories);
  assert.deepEqual(updateResult.model.fitur, []);
  assert.equal(updateResult.model.fitur_meta.origin, "user");
  assert.equal(updateResult.model.fitur_meta.user_locked, true);
});

test("empty user-locked bullets survive non-empty research and create pending feature_suggestions", () => {
  const locked = mutateModelDocument(modelDocument(), {
    action: "set_features",
    model_id: "AQUA::MODEL-1",
    fitur: null,
  }, categories).data;
  const researched = mutateModelDocument(locked, {
    action: "submit_research_features",
    model_id: "AQUA::MODEL-1",
    entry: {
      fitur: ["Bullet hasil riset"],
      source_url: "https://example.com/model-1/features",
      source_kind: "brand_official",
      verified_at: "2026-08-21T10:00:00+07:00",
    },
  }, categories);
  assert.deepEqual(researched.model.fitur, []);
  assert.equal(researched.model.fitur_meta.origin, "user");
  assert.equal(researched.model.fitur_meta.user_locked, true);
  assert.equal(researched.model.feature_suggestions.length, 1);
  assert.deepEqual(researched.model.feature_suggestions[0].fitur, ["Bullet hasil riset"]);
  assert.equal(researched.model.feature_suggestions[0].status, "pending");
});

function documentWithPendingFeatureSuggestion() {
  const locked = mutateModelDocument(modelDocument(), {
    action: "set_features",
    model_id: "AQUA::MODEL-1",
    fitur: ["Bullet user"],
  }, categories).data;
  return mutateModelDocument(locked, {
    action: "submit_research_features",
    model_id: "AQUA::MODEL-1",
    entry: {
      fitur: ["Bullet riset"],
      source_url: "https://example.com/model-1/features",
      source_kind: "brand_official",
      verified_at: "2026-08-21T10:00:00+07:00",
    },
  }, categories).data;
}

test("accept_feature_suggestion explicitly replaces bullets and keeps provenance under user lock", () => {
  const accepted = mutateModelDocument(documentWithPendingFeatureSuggestion(), {
    action: "accept_feature_suggestion",
    model_id: "AQUA::MODEL-1",
    suggestion_index: 0,
  }, categories, "2026-08-21T11:00:00+07:00");
  assert.deepEqual(accepted.model.fitur, ["Bullet riset"]);
  assert.equal(accepted.model.fitur_meta.origin, "user");
  assert.equal(accepted.model.fitur_meta.user_locked, true);
  assert.equal(accepted.model.fitur_meta.source_kind, "brand_official");
  assert.equal(accepted.model.feature_suggestions[0].status, "accepted");
});

test("reject_feature_suggestion explicitly leaves user bullets untouched", () => {
  const rejected = mutateModelDocument(documentWithPendingFeatureSuggestion(), {
    action: "reject_feature_suggestion",
    model_id: "AQUA::MODEL-1",
    suggestion_index: 0,
  }, categories, "2026-08-21T11:00:00+07:00");
  assert.deepEqual(rejected.model.fitur, ["Bullet user"]);
  assert.equal(rejected.model.feature_suggestions[0].status, "rejected");
});

test("server validator rejects invalid fitur_meta and feature_suggestions provenance", () => {
  const invalidMeta = modelDocument();
  invalidMeta.brands[0].models[0].fitur_meta = {
    source_url: null,
    source_kind: null,
    verified_at: null,
    origin: "user",
    user_locked: false,
  };
  invalidMeta.brands[0].models[0].feature_suggestions = [];
  assert.throws(() => mutateModelDocument(invalidMeta, {
    action: "set_spec_value",
    model_id: "AQUA::MODEL-1",
    key: "width_mm",
    value: 600,
  }, categories), /fitur edit user wajib user_locked=true/);

  const invalidSuggestion = modelDocument();
  invalidSuggestion.brands[0].models[0].feature_suggestions = [{
    fitur: ["Tidak aman"],
    source_url: "javascript:alert(1)",
    source_kind: "other",
    verified_at: "2026-08-21T10:00:00+07:00",
    origin: "research",
    status: "pending",
  }];
  assert.throws(() => mutateModelDocument(invalidSuggestion, {
    action: "set_spec_value",
    model_id: "AQUA::MODEL-1",
    key: "width_mm",
    value: 600,
  }, categories), /source_url invalid/);
});

test("Produk array 42 uses exact AQUA::model and PATCH /api/produk", async () => {
  const products = produkArray42();
  assert.throws(() => mutateModelDocument(products, {
    action: "set_features",
    model_id: "LG::PRODUK-42",
    fitur: ["Salah brand"],
  }, categories), (error) => error instanceof HttpError && error.status === 404);

  await withMockFetch(
    (call) => {
      if (call.method === "GET" && call.url.includes("produk-katalog.json")) return githubRead(products, "aaaaaaaa");
      if (call.method === "GET" && call.url.includes("spec-categories.json")) return githubRead(categories, "cccccccc");
      if (call.method === "PUT" && call.url.endsWith("/produk-katalog.json")) return githubWrite("dddddddd");
      throw new Error("unexpected mocked fetch: " + call.method + " " + call.url);
    },
    async (calls) => {
      const response = await patchProduk({
        request: new Request("https://local.test/api/produk", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify({
            action: "set_features",
            model_id: "AQUA::PRODUK-42",
            fitur: ["Bullet Produk"],
          }),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 200);
      const payload = await response.json();
      assert.equal(payload.model.model, "PRODUK-42");
      assert.equal(payload.model.fitur_meta.user_locked, true);
      assert.equal(calls.filter((call) => call.method === "GET" && call.url.includes("produk-katalog.json")).length, 1);
      assert.equal(calls.filter((call) => call.method === "PUT").length, 1);
    }
  );
});

test("full PUT Produk enriches legacy array and new model without losing legacy fields", async () => {
  const legacyProducts = [
    {
      model: "LEGACY-1",
      nama: "Produk lama",
      fitur: ["Bullet lama"],
      legacy_nested: { keep: true },
    },
    {
      model: "NEW-2",
      nama: "Produk baru",
      harga_idr: 123456,
    },
  ];

  await withMockFetch(
    (call) => {
      if (call.method === "GET" && call.url.includes("produk-katalog.json")) {
        return githubRead([legacyProducts[0]], "aaaaaaaa");
      }
      if (call.method === "GET" && call.url.includes("spec-categories.json")) {
        return githubRead(categories, "cccccccc");
      }
      if (call.method === "PUT" && call.url.endsWith("/produk-katalog.json")) {
        return githubWrite("dddddddd");
      }
      throw new Error("unexpected mocked fetch: " + call.method + " " + call.url);
    },
    async (calls) => {
      const response = await putProduk({
        request: new Request("https://local.test/api/produk", {
          method: "PUT",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify(legacyProducts),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 200);

      const writes = calls.filter((call) => call.method === "PUT");
      assert.equal(writes.length, 1);
      const writeBody = JSON.parse(writes[0].options.body);
      const written = JSON.parse(Buffer.from(writeBody.content, "base64").toString("utf8"));
      assert.equal(writeBody.sha, "aaaaaaaa");
      assert.equal(written.length, 2);

      assert.equal(written[0].model_id, "AQUA::LEGACY-1");
      assert.deepEqual(written[0].spec_values, {});
      assert.deepEqual(written[0].research_suggestions, []);
      assert.deepEqual(written[0].fitur, ["Bullet lama"]);
      assert.equal(written[0].fitur_meta.origin, "legacy");
      assert.equal(written[0].fitur_meta.user_locked, false);
      assert.deepEqual(written[0].feature_suggestions, []);
      assert.equal(written[0].nama, "Produk lama");
      assert.deepEqual(written[0].legacy_nested, { keep: true });

      assert.equal(written[1].model_id, "AQUA::NEW-2");
      assert.deepEqual(written[1].spec_values, {});
      assert.deepEqual(written[1].research_suggestions, []);
      assert.deepEqual(written[1].fitur, []);
      assert.equal(written[1].fitur_meta.origin, "unknown");
      assert.equal(written[1].fitur_meta.user_locked, false);
      assert.deepEqual(written[1].feature_suggestions, []);
      assert.equal(written[1].nama, "Produk baru");
      assert.equal(written[1].harga_idr, 123456);
    }
  );
});

test("full PUT Produk rejects orphan or invalid dynamic state with zero write", async () => {
  const validMeta = {
    source_url: null,
    source_kind: null,
    verified_at: null,
    origin: "unknown",
    user_locked: false,
  };
  const invalidPayloads = [
    [{
      model: "ORPHAN-1",
      model_id: "AQUA::ORPHAN-1",
      fitur: [],
      fitur_meta: validMeta,
      feature_suggestions: [],
      spec_values: {
        category_that_does_not_exist: {
          value: "orphan",
          source_url: null,
          source_kind: null,
          verified_at: null,
          origin: "legacy",
          user_locked: false,
        },
      },
      research_suggestions: [],
    }],
    [{
      model: "INVALID-1",
      model_id: "AQUA::INVALID-1",
      fitur: ["Bullet user"],
      fitur_meta: { ...validMeta, origin: "user", user_locked: false },
      feature_suggestions: [],
      spec_values: {},
      research_suggestions: [],
    }],
  ];

  for (const payload of invalidPayloads) {
    await withMockFetch(
      (call) => {
        if (call.method === "GET" && call.url.includes("produk-katalog.json")) {
          return githubRead([{ model: "CURRENT" }], "aaaaaaaa");
        }
        if (call.method === "GET" && call.url.includes("spec-categories.json")) {
          return githubRead(categories, "cccccccc");
        }
        throw new Error("GitHub write must stay zero for invalid full PUT");
      },
      async (calls) => {
        const response = await putProduk({
          request: new Request("https://local.test/api/produk", {
            method: "PUT",
            headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
            body: JSON.stringify(payload),
          }),
          env: { GITHUB_TOKEN: "fake-token" },
        });
        assert.equal(response.status, 400);
        assert.match((await response.json()).error, /orphan|kategori|fitur|user_locked/i);
        assert.equal(calls.filter((call) => call.method === "PUT").length, 0);
      }
    );
  }
});

test("full PUT Produk stale SHA returns 412 with zero write before category read", async () => {
  await withMockFetch(
    (call) => {
      if (call.method === "GET" && call.url.includes("produk-katalog.json")) {
        return githubRead([{ model: "CURRENT" }], "bbbbbbbb");
      }
      throw new Error("stale SHA must stop before category read or GitHub write");
    },
    async (calls) => {
      const response = await putProduk({
        request: new Request("https://local.test/api/produk", {
          method: "PUT",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify([{ model: "LEGACY-STALE", fitur: ["Tetap legacy"] }]),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 412);
      assert.equal(calls.filter((call) => call.method === "GET").length, 1);
      assert.equal(calls.filter((call) => call.method === "PUT").length, 0);
    }
  );
});

test("full PUT transition rejects empty payload, 50% mass removal, and brand removal", () => {
  const fourProducts = [
    { model: "P-1" },
    { model: "P-2" },
    { model: "P-3" },
    { model: "P-4" },
  ];
  assert.throws(
    () => validateDocumentTransition(fourProducts, []),
    (error) => error instanceof HttpError && error.status === 400 && /empty payload|dokumen kosong/i.test(error.message)
  );
  assert.throws(
    () => validateDocumentTransition(fourProducts, fourProducts.slice(0, 2)),
    (error) => error instanceof HttpError && error.status === 400 && /50%|mass removal/i.test(error.message)
  );

  const brands = {
    brands: [
      { brand: "AQUA", models: [{ model: "A-1" }] },
      { brand: "LG", models: [{ model: "L-1" }] },
    ],
    groups: [{ aqua: "A-1", competitors: { LG: "L-1" } }],
  };
  const missingBrand = structuredClone(brands);
  missingBrand.brands.pop();
  assert.throws(
    () => validateDocumentTransition(brands, missingBrand),
    (error) => error instanceof HttpError && error.status === 400 && /brand/i.test(error.message)
  );
});

test("full PUT transition preserves legitimate exact one-model edit", () => {
  const before = [{ model: "P-1", nama: "Lama" }, { model: "P-2", nama: "Tetap" }];
  const after = structuredClone(before);
  after[0].nama = "Baru";
  assert.deepEqual(validateDocumentTransition(before, after), {
    type: "edit",
    before_id: "AQUA::P-1",
    after_id: "AQUA::P-1",
  });
});

test("full PUT transition accepts one delete but rejects two model edits", () => {
  const before = [
    { model: "P-1", nama: "Satu" },
    { model: "P-2", nama: "Dua" },
    { model: "P-3", nama: "Tiga" },
    { model: "P-4", nama: "Empat" },
  ];
  assert.deepEqual(validateDocumentTransition(before, before.slice(0, 3)), {
    type: "delete",
    before_id: "AQUA::P-4",
    after_id: null,
  });
  const twoEdits = structuredClone(before);
  twoEdits[0].nama = "Satu berubah";
  twoEdits[1].nama = "Dua berubah";
  assert.throws(
    () => validateDocumentTransition(before, twoEdits),
    (error) => error instanceof HttpError && error.status === 400 && /tepat satu model/i.test(error.message)
  );
});

test("full PUT endpoint rejects two model edits with zero write", async () => {
  const current = [
    { model: "P-1", nama: "Satu" },
    { model: "P-2", nama: "Dua" },
    { model: "P-3", nama: "Tiga" },
  ];
  const payload = structuredClone(current);
  payload[0].nama = "Satu berubah";
  payload[1].nama = "Dua berubah";
  await withMockFetch(
    (call) => {
      if (call.method === "GET" && call.url.includes("produk-katalog.json")) {
        return githubRead(current, "aaaaaaaa");
      }
      throw new Error("multi-edit must stop before category read or GitHub write");
    },
    async (calls) => {
      const response = await putProduk({
        request: new Request("https://local.test/api/produk", {
          method: "PUT",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify(payload),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 400);
      assert.equal(calls.filter((call) => call.method === "GET").length, 1);
      assert.equal(calls.filter((call) => call.method === "PUT").length, 0);
    }
  );
});

test("legacy Produk UI keeps derived foto_list out of realistic 42-item full PUT", async () => {
  const source = await readFile(new URL("../site/js/produk.js", import.meta.url), "utf8");
  const sandbox = { URL, URLSearchParams };
  vm.runInNewContext(source, sandbox, { filename: "produk.js" });
  assert.equal(typeof sandbox.attachDerivedFotoList, "function");

  const current = produkArray42();
  const clientItems = structuredClone(current);
  clientItems.forEach((item, index) => {
    sandbox.attachDerivedFotoList(item, ["assets/produk/P-" + index + ".jpg"]);
  });
  clientItems[17].benefit = "tepat satu edit user";
  const payload = JSON.parse(JSON.stringify(clientItems));
  assert.equal(payload.every((item) => !Object.hasOwn(item, "foto_list")), true);

  await withMockFetch(
    (call) => {
      if (call.method === "GET" && call.url.includes("produk-katalog.json")) {
        return githubRead(current, "aaaaaaaa");
      }
      if (call.method === "GET" && call.url.includes("spec-categories.json")) {
        return githubRead(categories, "cccccccc");
      }
      if (call.method === "PUT" && call.url.endsWith("/produk-katalog.json")) {
        return githubWrite("dddddddd");
      }
      throw new Error("unexpected mocked fetch: " + call.method + " " + call.url);
    },
    async (calls) => {
      const response = await putProduk({
        request: new Request("https://local.test/api/produk", {
          method: "PUT",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify(payload),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 200);
      assert.equal(calls.filter((call) => call.method === "PUT").length, 1);
    }
  );
});

test("stored competitor media URL rejects data and javascript with zero write", async () => {
  const current = {
    brands: [{ brand: "AQUA", models: [{ model: "A-1", image: "assets/produk/a-1.jpg" }] }],
    groups: [{ aqua: "A-1", competitors: {} }],
  };
  for (const unsafe of ["data:image/png;base64,AAAA", "javascript:alert(1)"]) {
    const payload = structuredClone(current);
    payload.brands[0].models[0].image = unsafe;
    await withMockFetch(
      (call) => {
        if (call.method === "GET" && call.url.includes("kompetitor.json")) {
          return githubRead(current, "aaaaaaaa");
        }
        if (call.method === "GET" && call.url.includes("spec-categories.json")) {
          return githubRead(categories, "cccccccc");
        }
        if (call.method === "PUT") return githubWrite("dddddddd");
        throw new Error("unexpected mocked fetch: " + call.method + " " + call.url);
      },
      async (calls) => {
        const response = await putCompetitor({
          request: new Request("https://local.test/api/kompetitor", {
            method: "PUT",
            headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
            body: JSON.stringify(payload),
          }),
          env: { GITHUB_TOKEN: "fake-token" },
        });
        assert.equal(response.status, 400);
        assert.equal(calls.filter((call) => call.method === "PUT").length, 0);
      }
    );
  }
});

test("stored competitor media URL allowlist accepts https and same-origin relative paths", async () => {
  for (const safe of ["https://cdn.example.test/model.jpg", "assets/kompetitor/model-baru.jpg"]) {
    const current = {
      brands: [{ brand: "AQUA", models: [{ model: "A-1", image: "assets/kompetitor/model-lama.jpg" }] }],
      groups: [{ aqua: "A-1", competitors: {} }],
    };
    const payload = structuredClone(current);
    payload.brands[0].models[0].image = safe;
    await withMockFetch(
      (call) => {
        if (call.method === "GET" && call.url.includes("kompetitor.json")) {
          return githubRead(current, "aaaaaaaa");
        }
        if (call.method === "GET" && call.url.includes("spec-categories.json")) {
          return githubRead(categories, "cccccccc");
        }
        if (call.method === "PUT" && call.url.endsWith("/kompetitor.json")) {
          return githubWrite("dddddddd");
        }
        throw new Error("unexpected mocked fetch: " + call.method + " " + call.url);
      },
      async (calls) => {
        const response = await putCompetitor({
          request: new Request("https://local.test/api/kompetitor", {
            method: "PUT",
            headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
            body: JSON.stringify(payload),
          }),
          env: { GITHUB_TOKEN: "fake-token" },
        });
        assert.equal(response.status, 200);
        assert.equal(calls.filter((call) => call.method === "PUT").length, 1);
      }
    );
  }
});

test("recursive bounds reject oversized payload before any endpoint read or write", async () => {
  const oversized = [{ model: "P-1", benefit: "x".repeat(2 * 1024 * 1024 + 1) }];
  assert.throws(
    () => validateRecursiveBounds(oversized),
    (error) => error instanceof HttpError && error.status === 413 && /terlalu besar|terlalu panjang/i.test(error.message)
  );
  await withMockFetch(
    () => { throw new Error("oversized payload must perform zero network calls"); },
    async (calls) => {
      const response = await putProduk({
        request: new Request("https://local.test/api/produk", {
          method: "PUT",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify(oversized),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 413);
      assert.equal(calls.length, 0);
    }
  );
});

test("Kompetitor save lock serializes race and invalidates stale completion", async () => {
  const source = await readFile(new URL("../site/js/kompetitor-save-lock.js", import.meta.url), "utf8");
  const sandbox = {};
  vm.runInNewContext(source, sandbox, { filename: "kompetitor-save-lock.js" });
  const lock = sandbox.MTMSCompetitorSaveLock.create();
  const first = lock.begin();
  assert.equal(first, 1);
  assert.equal(lock.begin(), 0, "save kedua wajib ditolak selama save pertama berjalan");
  assert.equal(lock.isCurrent(first), true);
  assert.equal(lock.finish(first + 1), false, "completion asing tidak boleh membuka lock");
  lock.invalidate();
  assert.equal(lock.isCurrent(first), false, "completion lama wajib menjadi stale setelah invalidation");
  assert.equal(lock.finish(first), false);
  const next = lock.begin();
  assert.equal(next > first, true);
  assert.equal(lock.finish(next), true);
  assert.deepEqual({ ...lock.state() }, { busy: false, sequence: next });
});

test("Kompetitor 412 clears SHA and live gate then invalidates sequence before reload", async () => {
  const source = await readFile(new URL("../site/kompetitor.html", import.meta.url), "utf8");
  const start = source.indexOf("if(result.status===412)");
  const end = source.indexOf("return;", start);
  assert.notEqual(start, -1, "branch 412 wajib ada");
  assert.notEqual(end, -1, "branch 412 wajib berhenti setelah menjadwalkan reload");
  const branch = source.slice(start, end);
  const orderedTokens = [
    'compSha=""',
    "liveReady=false",
    "window.MTMS_COMPETITOR_LIVE_READY=false",
    "invalidateSaveSequence()",
    "window.location.reload()",
  ];
  let prior = -1;
  for (const token of orderedTokens) {
    const position = branch.indexOf(token);
    assert.equal(position > prior, true, token + " wajib terjadi berurutan sebelum reload");
    prior = position;
  }
});

function documentWithPendingSuggestion() {
  const source = modelDocument();
  source.brands[0].models[0].spec_values.width_mm = {
    value: 600,
    source_url: null,
    source_kind: null,
    verified_at: null,
    origin: "user",
    user_locked: true,
  };
  source.brands[0].models[0].research_suggestions.push({
    key: "width_mm",
    value: 610,
    source_url: "https://example.com/model-1",
    source_kind: "brand_official",
    verified_at: "2026-08-21T10:00:00+07:00",
    origin: "research",
    status: "pending",
  });
  return source;
}

test("accept suggestion is explicit and locks accepted value as user edit", () => {
  const accepted = mutateModelDocument(documentWithPendingSuggestion(), {
    action: "accept_suggestion",
    model_id: "AQUA::MODEL-1",
    suggestion_index: 0,
  }, categories, "2026-08-21T11:00:00+07:00");
  assert.equal(accepted.model.spec_values.width_mm.value, 610);
  assert.equal(accepted.model.spec_values.width_mm.origin, "user");
  assert.equal(accepted.model.spec_values.width_mm.user_locked, true);
  assert.equal(accepted.model.research_suggestions[0].status, "accepted");
});

test("reject suggestion is explicit and leaves current value untouched", () => {
  const rejected = mutateModelDocument(documentWithPendingSuggestion(), {
    action: "reject_suggestion",
    model_id: "AQUA::MODEL-1",
    suggestion_index: 0,
  }, categories, "2026-08-21T11:00:00+07:00");
  assert.equal(rejected.model.spec_values.width_mm.value, 600);
  assert.equal(rejected.model.research_suggestions[0].status, "rejected");
});

test("core key cannot be renamed or disabled; additional category key stays immutable to avoid orphan", () => {
  assert.throws(() => mutateCategories(categories, {
    action: "update_category",
    key: "form_factor",
    patch: { active: false },
  }), (error) => error instanceof HttpError && error.status === 400);

  const extended = mutateCategories(categories, {
    action: "create_category",
    category: {
      key: "ice_maker",
      label: "Ice Maker",
      group: "Tambahan",
      unit: "-",
      comparison: false,
      order: 130,
      active: true,
    },
  });
  assert.throws(() => mutateCategories(extended, {
    action: "update_category",
    key: "ice_maker",
    patch: { key: "ice_dispenser" },
  }), /immutable|orphan/i);
});

test("no-live-write proof: endpoint fetch is fully mocked at the network boundary", async () => {
  const original = modelDocument();
  await withMockFetch(
    (call) => {
      if (call.method === "GET" && call.url.includes("kompetitor.json")) return githubRead(original, "aaaaaaaa");
      if (call.method === "GET" && call.url.includes("spec-categories.json")) return githubRead(categories, "cccccccc");
      if (call.method === "PUT" && call.url.endsWith("/kompetitor.json")) return githubWrite("dddddddd");
      throw new Error("unexpected mocked fetch: " + call.method + " " + call.url);
    },
    async (calls) => {
      const response = await patchCompetitor({
        request: new Request("https://local.test/api/kompetitor", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", "If-Match": '"aaaaaaaa"' },
          body: JSON.stringify({
            action: "update_model",
            model_id: "AQUA::MODEL-1",
            fitur: ["Bullet user"],
            spec_values: { door_count: 2 },
          }),
        }),
        env: { GITHUB_TOKEN: "fake-token" },
      });
      assert.equal(response.status, 200);
      const payload = await response.json();
      assert.equal(payload.sha, "dddddddd");
      assert.equal(payload.model.fitur[0], "Bullet user");
      assert.equal(payload.model.fitur_meta.origin, "user");
      assert.equal(payload.model.fitur_meta.user_locked, true);
      assert.equal(payload.model.spec_values.door_count.user_locked, true);
      assert.equal(calls.filter((call) => call.method === "PUT").length, 1);
      const writeBody = JSON.parse(calls.find((call) => call.method === "PUT").options.body);
      assert.equal(writeBody.sha, "aaaaaaaa");
    }
  );
});

test("editor markup and wiring covers live SHA gate, exact model, values, bullets, suggestions, and global categories", async () => {
  const [html, produkHtml, produkJs, javascript, css] = await Promise.all([
    readFile(new URL("../site/kompetitor.html", import.meta.url), "utf8"),
    readFile(new URL("../site/produk.html", import.meta.url), "utf8"),
    readFile(new URL("../site/js/produk.js", import.meta.url), "utf8"),
    readFile(new URL("../site/js/dynamic-spec-editor.js", import.meta.url), "utf8"),
    readFile(new URL("../site/css/style.css", import.meta.url), "utf8"),
  ]);
  assert.match(html, /src="js\/dynamic-spec-editor\.js"/);
  assert.match(html, /dataUrl:\s*"api\/kompetitor"/);
  assert.match(html, /categoriesUrl:\s*"api\/spec-categories"/);
  assert.match(produkHtml, /src="js\/dynamic-spec-editor\.js"/);
  assert.match(produkJs, /dataUrl:\s*"api\/produk"/);
  assert.match(produkJs, /initialData:\s*liveItems/);
  assert.match(produkJs, /initialSha:\s*window\.MTMS_PRODUCTS_SHA/);

  [
    "button.disabled = true",
    "data-live-ready",
    "data-ds-model-select",
    "data-ds-spec-key",
    "data-ds-features",
    "research_suggestions",
    "fitur_meta",
    "feature_suggestions",
    'data-ds-suggestion="accept"',
    'data-ds-suggestion="reject"',
    'data-ds-feature-suggestion="accept"',
    'data-ds-feature-suggestion="reject"',
    "data-ds-create-category",
    'name="active"',
    'name="order"',
    'name="comparison"',
    "X-Data-SHA",
    "ETag",
    "If-Match",
    'method: "PATCH"',
    "STALE SHA",
  ].forEach((needle) => assert.ok(javascript.includes(needle), `missing editor wiring: ${needle}`));
  [".ds-editor-fab", ".ds-editor-panel", ".ds-spec-row", ".ds-suggestion", ".ds-category-card"]
    .forEach((selector) => assert.ok(css.includes(selector), `missing editor style: ${selector}`));
});

test("initial payload reuse has no duplicate model GET and fetch call count is categories-only", async () => {
  const source = await readFile(new URL("../site/js/dynamic-spec-editor.js", import.meta.url), "utf8");
  const sandbox = { window: {}, document: {} };
  vm.runInNewContext(source, sandbox, { filename: "dynamic-spec-editor.js" });

  const initialData = produkArray42();
  const calls = [];
  const loaded = await sandbox.window.MTMSDynamicSpecEditor._loadInitialData(
    initialData,
    "aaaaaaaa",
    "api/spec-categories",
    async (url) => {
      calls.push(url);
      return { payload: categories, sha: "bbbbbbbb" };
    }
  );
  assert.deepEqual(calls, ["api/spec-categories"]);
  assert.equal(calls.some((url) => url === "api/produk" || url === "api/kompetitor"), false);
  const rows = sandbox.window.MTMSDynamicSpecEditor._flattenModels(loaded[0].payload);
  assert.equal(rows.length, 42);
  assert.equal(rows[41].modelId, "AQUA::PRODUK-42");

  const noShaCalls = [];
  await assert.rejects(
    sandbox.window.MTMSDynamicSpecEditor._loadInitialData(
      initialData,
      "",
      "api/spec-categories",
      async (url) => {
        noShaCalls.push(url);
        return { payload: categories, sha: "bbbbbbbb" };
      }
    ),
    /SHA/
  );
  assert.deepEqual(noShaCalls, []);
});
