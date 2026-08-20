// Pages Function: GET/PUT /api/kompetitor
// Baca/tulis kompetitor.json dari repo data GitHub.
// Mirip /api/produk tapi untuk data perbandingan kompetitor.

const OWNER = "Louisfernaldi";
const REPO = "mtms-aqua-haier-kb-data";
const BRANCH = "main";
const DATA_FILE = "kompetitor.json";

async function ghReq(env, path, opts = {}) {
  const base = "https://api.github.com/repos/" + OWNER + "/" + REPO + "/contents/" + path;
  const headers = {
    Authorization: "Bearer " + env.GITHUB_TOKEN,
    Accept: "application/vnd.github+json",
    "User-Agent": "mtms-kb",
    "Content-Type": "application/json",
  };
  if (opts.headers) Object.assign(headers, opts.headers);
  return fetch(base + (opts.query || ""), { ...opts, headers });
}

async function readData(env) {
  const res = await ghReq(env, DATA_FILE, { method: "GET", query: "?ref=" + BRANCH });
  if (!res.ok) throw new Error("GH_READ_" + res.status);
  const meta = await res.json();
  const bytes = Uint8Array.from(atob(meta.content.replace(/\n/g, "")), function (c) { return c.charCodeAt(0); });
  const decoded = new TextDecoder().decode(bytes);
  return { data: JSON.parse(decoded), sha: meta.sha };
}

export async function onRequestGet(context) {
  const { env } = context;
  try {
    const { data } = await readData(env);
    return new Response(JSON.stringify(data), {
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
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: "bad json" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }
  if (!body || !body.brands || !Array.isArray(body.brands)) {
    return new Response(JSON.stringify({ error: "invalid payload: need {brands: [...]} " }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }
  try {
    const { sha } = await readData(env);
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(body, null, 2))));
    const res = await ghReq(env, DATA_FILE, {
      method: "PUT",
      body: JSON.stringify({
        message: "update kompetitor via editor web",
        content: encoded,
        sha,
        branch: BRANCH,
      }),
    });
    if (!res.ok) throw new Error("GH_WRITE_" + res.status);
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
