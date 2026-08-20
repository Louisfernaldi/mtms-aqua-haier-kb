// _lib/config.js — baca/tulis konfigurasi situs (site-config.json) di repo data GitHub.
// Password login disimpan di GitHub supaya bisa diganti dari website (Pages secret
// tidak bisa diubah lewat fungsi). Cache per-isolate 15 detik; fallback env.LOGIN_PASSWORD.
const REPO = "Louisfernaldi/mtms-aqua-haier-kb-data";
const CFG_PATH = "site-config.json";
const CFG_REF = "main";

let cfgCache = { password: null, sha: null, ttl: 0 };

function b64enc(s) {
  var bytes = new TextEncoder().encode(s);
  return btoa(String.fromCharCode.apply(null, bytes));
}
function b64dec(s) {
  var bytes = Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); });
  return new TextDecoder().decode(bytes);
}

async function fetchConfig(env) {
  var url = "https://api.github.com/repos/" + REPO + "/contents/" + CFG_PATH + "?ref=" + CFG_REF;
  var res = await fetch(url, {
    headers: {
      Authorization: "Bearer " + env.GITHUB_TOKEN,
      Accept: "application/vnd.github+json",
      "User-Agent": "mtms-kb",
    },
  });
  if (!res.ok) throw new Error("cfg_" + res.status);
  var meta = await res.json();
  var cfg = JSON.parse(b64dec(meta.content));
  return { password: String(cfg.login_password || ""), sha: meta.sha };
}

export async function getLoginPassword(env) {
  var now = Date.now();
  if (cfgCache.password !== null && now < cfgCache.ttl) return cfgCache.password;
  try {
    var c = await fetchConfig(env);
    cfgCache = { password: c.password, sha: c.sha, ttl: now + 15000 };
  } catch (e) {
    if (env.LOGIN_PASSWORD) {
      cfgCache = { password: env.LOGIN_PASSWORD, sha: null, ttl: now + 15000 };
    }
  }
  return cfgCache.password;
}

export async function changeLoginPassword(env, newPassword) {
  var sha = cfgCache.sha;
  if (!sha) {
    try { var c = await fetchConfig(env); sha = c.sha; } catch (e) { sha = null; }
  }
  var content = b64enc(JSON.stringify({ login_password: newPassword }));
  var payload = { message: "ubah password login situs (dari website)", content: content };
  if (sha) payload.sha = sha;
  var res = await fetch("https://api.github.com/repos/" + REPO + "/contents/" + CFG_PATH, {
    method: "PUT",
    headers: {
      Authorization: "Bearer " + env.GITHUB_TOKEN,
      Accept: "application/vnd.github+json",
      "User-Agent": "mtms-kb",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("write_" + res.status);
  // invalidate cache supaya perubahan langsung kebaca
  cfgCache = { password: null, sha: null, ttl: 0 };
  return true;
}

// hash cookie = SHA-256(password + GITHUB_TOKEN) supaya ganti password
// otomatis membatalkan semua sesi lama.
export async function authHash(secret, env) {
  var data = new TextEncoder().encode(String(secret) + "|" + (env.GITHUB_TOKEN || ""));
  var buf = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(buf)).map(function (b) {
    return ("0" + b.toString(16)).slice(-2);
  }).join("");
}