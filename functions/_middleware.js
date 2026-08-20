// _middleware.js — gerbang login seluruh situs.
// Publik (tanpa login): halaman login (/login atau /login.html), api login/logout,
//   css, assets, favicon, dan js KECUALI js/data.js (isi konten).
// Semua path lain dikunci: belum login -> redirect /login (html) atau 401 (api).
// Cookie = hash(password) -> ganti password otomatis membatalkan semua sesi lama.
// Catatan: Cloudflare Pages men-308 /xxx.html -> /xxx (extensionless), jadi gating-nya
//   berbasis "bukan publik" biar /produk, /induksi, dst. ikut terkunci.
import { getLoginPassword, authHash } from "./_lib/config.js";

const AUTH_COOKIE = "mtms_auth";

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  const isPublic = (
    path === "/login" || path === "/login.html" ||
    path === "/api/login" || path === "/api/logout" ||
    path === "/favicon.svg" ||
    path.startsWith("/css/") ||
    path.startsWith("/assets/") ||
    (path.startsWith("/js/") && path !== "/js/data.js")
  );
  if (isPublic) return context.next();

  const cookie = request.headers.get("Cookie") || "";
  let authed = false;
  try {
    const pw = await getLoginPassword(env);
    const expected = await authHash(pw, env);
    authed = cookie.split(";").some(function (c) {
      return c.trim() === AUTH_COOKIE + "=" + expected;
    });
  } catch (e) {
    authed = false;
  }
  if (authed) return context.next();

  if (path.startsWith("/api/")) {
    return new Response(JSON.stringify({ error: "login required" }), {
      status: 401,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }
  const next = encodeURIComponent(path);
  return new Response(null, {
    status: 302,
    headers: { Location: "/login?next=" + next, "Cache-Control": "no-store" },
  });
}