# -*- coding: utf-8 -*-
import asyncio, base64, io, json, os
from playwright.async_api import async_playwright
from PIL import Image

BASE = "http://127.0.0.1:" + os.environ.get("PORT", "8788")
PASS = "aquaisthebest"
NEWPASS = "testpass99"

buf = io.BytesIO()
Image.new("RGB", (70, 50), (30, 120, 220)).save(buf, "JPEG", quality=70)
TEST_IMG = base64.b64encode(buf.getvalue()).decode()
TEST_FOTO = "AQR-TESTSLOT2__web0.jpg"

async def jpost(r):
    t = {}
    try:
        txt = await r.text()
        t = json.loads(txt) if txt else {}
    except Exception:
        t = {}
    return {"status": r.status, "json": t}

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

        # --- login salah -> 401
        r = await pg.request.post(BASE + "/api/login", data=json.dumps({"password": "salah123"}))
        print("1) login password salah:", r.status)

        # --- login benar
        r = await pg.request.post(BASE + "/api/login", data=json.dumps({"password": PASS}))
        cookies = await pg.context.cookies()
        print("2) login benar:", r.status, "| cookie ada:", any(c["name"] == "mtms_auth" for c in cookies))
        r = await pg.request.get(BASE + "/api/produk")
        print("3) api/produk dengan cookie valid:", r.status)

        # --- tombol ganti password & modal
        await pg.goto(BASE + "/produk.html", wait_until="networkidle")
        await pg.wait_for_timeout(1200)
        n_btn = await pg.eval_on_selector_all(".pk-edit-pass", "els => els.length")
        await pg.click(".pk-edit-pass")
        await pg.wait_for_timeout(600)
        n_fields = await pg.eval_on_selector_all("#pw_cur,#pw_new,#pw_new2", "els => els.length")
        print("4) tombol + modal ganti password:", n_btn, "tombol,", n_fields, "field")

        # --- ganti password: current salah
        r = await pg.request.post(BASE + "/api/password", data=json.dumps({"current": "salah", "password": NEWPASS, "confirm": NEWPASS}))
        print("5) current salah:", r.status, (await jpost(r))["json"].get("error"))
        # --- password baru pendek
        r = await pg.request.post(BASE + "/api/password", data=json.dumps({"current": PASS, "password": "abc", "confirm": "abc"}))
        print("6) password baru pendek:", r.status, (await jpost(r))["json"].get("error"))
        # --- confirm beda
        r = await pg.request.post(BASE + "/api/password", data=json.dumps({"current": PASS, "password": NEWPASS, "confirm": "beda99"}))
        print("7) confirm beda:", r.status, (await jpost(r))["json"].get("error"))
        # --- sukses
        r = await pg.request.post(BASE + "/api/password", data=json.dumps({"current": PASS, "password": NEWPASS, "confirm": NEWPASS}))
        print("8) ganti sukses:", r.status)

        # --- sesi lama harus mati
        r = await pg.request.get(BASE + "/api/produk")
        print("9) api/produk setelah ganti (sesi lama harus 401):", r.status)

        # --- login pakai password baru
        r = await pg.request.post(BASE + "/api/login", data=json.dumps({"password": NEWPASS}))
        print("10) login password baru:", r.status)
        r = await pg.request.get(BASE + "/api/produk")
        print("11) api/produk dengan password baru:", r.status)

        # --- restore password ke semula
        r = await pg.request.post(BASE + "/api/password", data=json.dumps({"current": NEWPASS, "password": PASS, "confirm": PASS}))
        print("12) restore password:", r.status)
        r = await pg.request.get(BASE + "/api/produk")
        print("13) api/produk (sesi baru-password mati):", r.status)
        r = await pg.request.post(BASE + "/api/login", data=json.dumps({"password": PASS}))
        print("14) login password semula:", r.status)
        r = await pg.request.get(BASE + "/api/produk")
        print("15) api/produk akhir:", r.status)
        cur = json.loads(await r.text())
        orig_obj = next(x for x in cur if x["model"] == "AQR-320RBG")

        # --- foto slot: buka edit AQR-320RBG
        await pg.reload(wait_until="networkidle")
        await pg.wait_for_timeout(1200)
        await pg.click('.pk-card[data-model="AQR-320RBG"] .pk-card-edit')
        await pg.wait_for_timeout(800)
        await pg.set_input_files("#f_up1", {
            "name": TEST_FOTO, "mimeType": "image/jpeg", "buffer": base64.b64decode(TEST_IMG)
        })
        await pg.wait_for_timeout(2500)
        slot2 = await pg.input_value("#f_foto_1")
        print("16) upload ke slot 2 -> nilai slot2:", slot2[:80] if slot2 else "(KOSONG)")
        fv = await pg.input_value("#f_fitur")
        await pg.fill("#f_fitur", (fv + "\nTES FITUR BARU").strip())
        await pg.click("#pk-edit-save")
        await pg.wait_for_timeout(2500)
        r = await pg.request.get(BASE + "/api/produk")
        d2 = json.loads(await r.text())
        upd = next(x for x in d2 if x["model"] == "AQR-320RBG")
        print("17) fitur ada:", "TES FITUR BARU" in (upd.get("fitur") or []), "| foto_list:", len(upd.get("foto_list") or []))
        # restore data asli
        d3 = [orig_obj if x["model"] == "AQR-320RBG" else x for x in d2]
        rc = await pg.request.put(BASE + "/api/produk", headers={"Content-Type": "application/json"}, data=json.dumps(d3))
        print("18) restore data:", rc.status)

        print("console errors:", len(errs), errs[:3])
        await b.close()

asyncio.run(main())


