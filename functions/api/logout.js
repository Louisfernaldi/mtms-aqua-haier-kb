// POST /api/logout — hapus cookie login.
export async function onRequestPost(context) {
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Set-Cookie": "mtms_auth=; Path=/; Max-Age=0; SameSite=Lax; HttpOnly",
      "Cache-Control": "no-store",
    },
  });
}