// POST /api/login — validasi password situs (dibaca dari GitHub via _lib/config),
// set cookie login = hash(password) supaya ganti password membatalkan sesi lama.
import { getLoginPassword, authHash } from "../_lib/config.js";

export async function onRequestPost(context) {
  const { request, env } = context;
  let body = {};
  try { body = await request.json(); } catch (e) {}
  const pw = await getLoginPassword(env);
  if (!pw || String(body.password || "") !== pw) {
    return new Response(JSON.stringify({ ok: false }), {
      status: 401,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }
  const cookie = "mtms_auth=" + (await authHash(pw, env)) + "; Path=/; Max-Age=7776000; SameSite=Lax; HttpOnly";
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "Content-Type": "application/json", "Set-Cookie": cookie, "Cache-Control": "no-store" },
  });
}

// GET /api/login?check=1 — cek status login (dipakai halaman login untuk auto-redirect)
export async function onRequestGet(context) {
  return new Response(JSON.stringify({ ok: true }), {
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}