// Pages Function: GET/POST /api/foto
// GET  -> daftar file foto dari repo publik mtms-aqua-haier-kb-foto (git trees API).
// POST -> upload foto (base64 JSON) ke repo foto, butuh X-Edit-Key = env.EDIT_PASSWORD.

const FOTO_OWNER = "Louisfernaldi";
const FOTO_REPO = "mtms-aqua-haier-kb-foto";

async function gh(env, url, opts = {}) {
  const headers = {
    Authorization: "Bearer " + env.GITHUB_TOKEN,
    Accept: "application/vnd.github+json",
    "User-Agent": "mtms-kb",
    ...(opts.headers || {}),
  };
  const res = await fetch(url, { ...opts, headers });
  return res;
}

export async function onRequestGet(context) {
  const { env } = context;
  const branch = env.FOTO_BRANCH || "main";
  try {
    const r = await gh(env, `https://api.github.com/repos/${FOTO_OWNER}/${FOTO_REPO}/git/trees/${branch}?recursive=1`);
    if (!r.ok) throw new Error("TREES_" + r.status + ": " + (await r.text()).slice(0, 150));
    const tree = await r.json();
    const files = (tree.tree || [])
      .filter(function (t) { return t.type === "blob" && t.path.indexOf("/") === -1 && /\.(jpg|jpeg|png|webp)$/i.test(t.path); })
      .map(function (t) { return t.path; });
    return new Response(JSON.stringify({ files }), {
      headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  // Autentikasi: middleware _middleware.js sudah mewajibkan login untuk /api/*.
  let body = {};
  try { body = await request.json(); } catch (e) {}
  const name = String(body.name || "").trim();
  const data = String(body.data || "");
  const safe = name.replace(/[^a-zA-Z0-9._-]/g, "_");
  if (!safe || safe.length > 200 || !/\.(jpg|jpeg|png|webp)$/i.test(safe)) {
    return new Response(JSON.stringify({ error: "nama file tidak valid" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }
  if (!/^[A-Za-z0-9+/=\s]+$/.test(data) || data.replace(/\s/g, "").length < 100) {
    return new Response(JSON.stringify({ error: "data gambar tidak valid" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }
  const branch = env.FOTO_BRANCH || "main";
  try {
    const enc = encodeURIComponent(safe);
    const url = `https://api.github.com/repos/${FOTO_OWNER}/${FOTO_REPO}/contents/${enc}`;
    let sha = null;
    const ex = await gh(env, url + `?ref=${branch}`);
    if (ex.ok) sha = (await ex.json()).sha;
    const put = await gh(env, url, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "upload foto via editor web",
        content: data.replace(/\s/g, ""),
        branch,
        sha,
      }),
    });
    if (!put.ok) throw new Error("PUT_" + put.status + ": " + (await put.text()).slice(0, 150));
    const ts = Date.now();
    return new Response(JSON.stringify({
      ok: true,
      url: `https://raw.githubusercontent.com/${FOTO_OWNER}/${FOTO_REPO}/${branch}/${safe}?v=${ts}`,
    }), { headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}