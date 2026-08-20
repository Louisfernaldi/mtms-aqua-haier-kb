# -*- coding: utf-8 -*-
import asyncio, base64, io, json, os
from playwright.async_api import async_playwright
from PIL import Image

BASE = "http://127.0.0.1:" + os.environ.get("PORT", "8788")
LOGIN = "aquaisthebest"

buf = io.BytesIO()
Image.new("RGB", (70, 50), (30, 120, 220)).save(buf, "JPEG", quality=70)
TEST_IMG = base64.b64encode(buf.getvalue()).decode()
TEST_FOTO = "AQR-TESTSLOT2__web0.jpg"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

        # login
        await pg.goto(BASE + "/login", wait_until="networkidle")
        await pg.fill("#login-pass", LOGIN)
        await pg.click("#login-go")
        await pg.wait_for_timeout(1500)

        await pg.goto(BASE + "/produk.html", wait_until="networkidle")
        await pg.wait_for_timeout(1500)

        # ambil data asli AQR-320RBG buat restore
        r = await pg.request.get(BASE + "/api/produk")
        data = await r.json()
        orig = next(x for x in data if x["model"] == "AQR-320RBG")

        # buka edit AQR-320RBG
        await pg.click('.pk-card[data-model="AQR-320RBG"] .pk-card-edit')
        await pg.wait_for_timeout(800)
        n_slots = await pg.eval_on_selector_all(".pk-foto-slot", "els => els.length")
        print("1) slot foto:", n_slots, "| ada select foto:", await pg.eval_on_selector_all("select.pk-foto-sel", "els => els.length"))
        fv = await pg.input_value("#f_fitur")
        print("2) fitur textarea awal:", repr(fv[:60]))

        # upload foto ke slot 2
        await pg.set_input_files("#f_up1", {
            "name": TEST_FOTO, "mimeType": "image/jpeg", "buffer": base64.b64decode(TEST_IMG)
        })
        await pg.wait_for_timeout(2500)
        slot2 = await pg.input_value("#f_foto_1")
        print("3) slot2 setelah upload:", slot2[:80])

        # edit fitur: tambah 1 poin
        new_fitur = fv + "\nTES FITUR BARU DARI EDITOR"
        await pg.fill("#f_fitur", new_fitur)
        await pg.click("#pk-edit-save")
        await pg.wait_for_timeout(2500)

        # verifikasi via API
        r2 = await pg.request.get(BASE + "/api/produk")
        data2 = await r2.json()
        upd = next(x for x in data2 if x["model"] == "AQR-320RBG")
        print("4) fitur baru ada:", "TES FITUR BARU DARI EDITOR" in (upd.get("fitur") or []))
        print("   foto_list length:", len(upd.get("foto_list") or []), "| foto:", (upd.get("foto") or "")[:70])

        # restore data asli (hapus tes)
        data2 = [orig if x["model"] == "AQR-320RBG" else x for x in data2]
        rc = await pg.request.put(BASE + "/api/produk", headers={"Content-Type": "application/json"}, data=json.dumps(data2))
        print("5) restore:", rc.status)

        print("console errors:", len(errs), errs[:3])
        await b.close()

asyncio.run(main())