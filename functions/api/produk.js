// Pages Function: GET/PUT /api/produk
// Baca/tulis produk-katalog.json dari repo GitHub privat (mtms-aqua-haier-kb-data).
// PUT butuh header X-Edit-Key = env.EDIT_PASSWORD. Local dev pakai .dev.vars (DATA_PATH bisa di-override).

const OWNER = "Louisfernaldi";
const REPO = "mtms-aqua-haier-kb-data";
const BRANCH = "main";
const DEFAULT_PATH = "produk-katalog.json";

async function ghRequest(env, path, options = {}) {
  const base = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}`;
  const headers = {
    Authorization: "Bearer " + env.GITHUB_TOKEN,
    Accept: "application/vnd.github+json",
    "User-Agent": "mtms-aqua-haier-kb",
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  const res = await fetch(base + (options.query || ""), { ...options, headers });
  return res;
}

async function readProducts(env) {
  const path = env.DATA_PATH || DEFAULT_PATH;
  const res = await ghRequest(env, path, {
    method: "GET",
    query: `?ref=${BRANCH}`,
  });
  if (!res.ok) {
    throw new Error("GH_READ_" + res.status + ": " + (await res.text()).slice(0, 160));
  }
  const meta = await res.json();
  const decoded = atob(meta.content.replace(/\n/g, ""));
  return { array: JSON.parse(decoded), sha: meta.sha, path };
}

export async function onRequestGet(context) {
  const { env } = context;
  try {
    const { array } = await readProducts(env);
    return new Response(JSON.stringify(array), {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=5",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }
}

export async function onRequestPut(context) {
  const { request, env } = context;
  // Autentikasi: middleware _middleware.js sudah mewajibkan login untuk /api/*.
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: "bad json" }), { status: 400, headers: { "Content-Type": "application/json" } });
  }
  if (!Array.isArray(body) || !body.every((p) => p && typeof p.model === "string")) {
    return new Response(JSON.stringify({ error: "invalid payload: harus array produk dengan field model" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }
  try {
    const { sha, path } = await readProducts(env);
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(body, null, 2))));
    const res = await ghRequest(env, path, {
      method: "PUT",
      query: "",
      body: JSON.stringify({
        message: "update produk via editor web (19 Agu 2026)",
        content: encoded,
        sha,
        branch: BRANCH,
      }),
    });
    if (!res.ok) {
      throw new Error("GH_WRITE_" + res.status + ": " + (await res.text()).slice(0, 160));
    }
    return new Response(JSON.stringify({ ok: true }), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }
}
