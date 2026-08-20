// POST /api/password — ganti password login situs (wajib login dulu via middleware).
// Body: { current, password, confirm }. Password baru >= 6 karakter.
import { getLoginPassword, changeLoginPassword } from "../_lib/config.js";

export async function onRequestPost(context) {
  const { request, env } = context;
  let body = {};
  try { body = await request.json(); } catch (e) {}
  const cur = String(body.current || "");
  const nw = String(body.password || "");
  const confirm = String(body.confirm || "");

  const pw = await getLoginPassword(env);
  if (cur !== pw) {
    return new Response(JSON.stringify({ error: "Password lama tidak sesuai." }), {
      status: 400,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }
  if (nw.length < 6) {
    return new Response(JSON.stringify({ error: "Password baru minimal 6 karakter." }), {
      status: 400,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }
  if (nw !== confirm) {
    return new Response(JSON.stringify({ error: "Password baru tidak sama dengan ulangannya." }), {
      status: 400,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }
  try {
    await changeLoginPassword(env, nw);
  } catch (e) {
    return new Response(JSON.stringify({ error: "Gagal menyimpan. Coba lagi nanti." }), {
      status: 500,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  }
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}