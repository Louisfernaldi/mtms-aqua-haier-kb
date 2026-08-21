# -*- coding: utf-8 -*-
"""Gerbang E2E komponen detail produk bersama. Read-only terhadap API/data."""
import asyncio
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.async_api import async_playwright


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
CATALOG_PATH = os.path.join(SITE, "data", "produk-katalog.json")
COMP_PATH = os.path.join(SITE, "data", "kompetitor.json")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PRICE_SOURCE_RAW = "price_gfk (brief)"
PRICE_SOURCE_DISPLAY = "price GfK (ringkasan riset)"
CARD_404_PATH = "/__verify_product_detail__/missing-card.png"
MODAL_404_PATH = "/__verify_product_detail__/missing-modal.png"


def fail(message):
    raise AssertionError(message)


def is_local_competitor_fixture(row):
    image = str(row.get("image") or "").replace("\\", "/")
    photo_url = str(row.get("photo_url") or "")
    if not image.startswith("assets/kompetitor/") or not photo_url.startswith(("http://", "https://")):
        return False
    local_path = os.path.normpath(os.path.join(SITE, image.replace("/", os.sep)))
    assets_root = os.path.normpath(os.path.join(SITE, "assets", "kompetitor"))
    return os.path.commonpath((local_path, assets_root)) == assets_root and os.path.isfile(local_path)


def fixtures():
    with open(CATALOG_PATH, encoding="utf-8") as fh:
        catalog = json.load(fh)
    with open(COMP_PATH, encoding="utf-8") as fh:
        embedded_comp = json.load(fh)
    if not embedded_comp.get("groups"):
        fail("Fixture gagal: data bawaan kompetitor tidak punya groups untuk render cepat")

    by_model = {row.get("model"): row for row in catalog}
    aqua_models = next(b["models"] for b in embedded_comp["brands"] if b["brand"] == "AQUA")
    aqua = next((row for row in aqua_models if row.get("model") == "AQR-DTM245CBP" and row.get("model") in by_model), None)
    if not aqua:
        fail("Fixture gagal: AQR-DTM245CBP tidak ada di katalog dan kompetitor")
    competitor = None
    competitor_brand = None
    for brand in embedded_comp["brands"]:
        if brand["brand"] == "AQUA":
            continue
        competitor = next((row for row in brand["models"] if row.get("cat") == aqua.get("cat") and row.get("price_source") == PRICE_SOURCE_RAW and row.get("fitur") and row.get("source_url") and is_local_competitor_fixture(row)), None)
        if competitor:
            competitor_brand = brand["brand"]
            break
    if not competitor:
        fail("Fixture gagal: tidak ada kompetitor satu kategori dengan price_gfk (brief), fitur, source, photo_url, dan aset lokal")

    canonical = json.loads(json.dumps(catalog))
    canonical_row = next(row for row in canonical if row.get("model") == aqua["model"])
    canonical_row["serie"] = "CANONICAL_SENTINEL_FROM_PRODUCT_API"
    canonical_row["material"] = "CANONICAL_MATERIAL_SENTINEL"

    # API kompetitor sengaja tipis. Implementasi wajib memperkaya dari embedded,
    # tetapi groups API ini wajib tetap dipertahankan.
    api_comp = json.loads(json.dumps(embedded_comp))
    api_comp["groups"] = [{
        "aqua": aqua["model"],
        "competitors": {competitor_brand: competitor["model"]},
    }]
    for brand in api_comp["brands"]:
        for row in brand["models"]:
            if brand["brand"] == competitor_brand and row.get("model") == competitor["model"]:
                row["fitur"] = []
                row["source_url"] = ""
                row["image"] = ""
                row["photo_url"] = ""
                row["price_source"] = ""
    return canonical, api_comp, aqua, competitor, competitor_brand


class Handler(SimpleHTTPRequestHandler):
    catalog = None
    competitor = None

    def log_message(self, *_args):
        pass

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in (CARD_404_PATH, MODAL_404_PATH):
            self.send_error(404)
            return
        if path == "/api/produk":
            return self._json(self.catalog)
        if path == "/api/kompetitor":
            return self._json(self.competitor)
        if path == "/api/foto":
            return self._json({"files": []})
        return super().do_GET()

    def do_PUT(self):
        return self._json({"error": "checker read-only: PUT dilarang"}, 405)

    def do_POST(self):
        return self._json({"error": "checker read-only: POST dilarang"}, 405)


async def wait_modal(page):
    modal = page.locator('.pk-modal.open[data-mtms-product-detail="true"]')
    await modal.wait_for(state="visible", timeout=5000)
    return modal


async def assert_clean(page, errors, label):
    overflow = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
    if overflow:
        fail(label + ": document melebar; horizontal scroll harus hanya di wrapper tabel")
    if errors:
        fail(label + ": console/page error: " + " | ".join(errors))


async def assert_local_loaded_image(page, image, label):
    await image.wait_for(state="visible", timeout=5000)
    handle = await image.element_handle()
    await page.wait_for_function("img => img.complete", arg=handle, timeout=5000)
    state = await image.evaluate("""img => {
        const absolute = img.currentSrc || img.src || "";
        const parsed = absolute ? new URL(absolute, window.location.href) : null;
        return {
            src: img.getAttribute("src") || "",
            absolute: absolute,
            complete: img.complete,
            naturalWidth: img.naturalWidth,
            sameOrigin: !!parsed && parsed.origin === window.location.origin,
            localPath: !!parsed && parsed.pathname.indexOf("/assets/kompetitor/") !== -1
        };
    }""")
    if not state["src"]:
        fail(label + ": src gambar kosong")
    if not state["complete"] or state["naturalWidth"] <= 0:
        fail(label + ": gambar belum selesai dimuat atau naturalWidth nol: " + json.dumps(state))
    if not state["sameOrigin"] or not state["localPath"] or not state["src"].replace("\\", "/").startswith("assets/kompetitor/"):
        fail(label + ": gambar bukan aset lokal same-origin assets/kompetitor: " + json.dumps(state))


async def assert_real_image_fallbacks(page, base, comp_trigger):
    card_url = base + CARD_404_PATH
    modal_url = base + MODAL_404_PATH
    try:
        card_image = comp_trigger.locator("img.comp-thumb")
        async with page.expect_response(lambda response: response.url == card_url) as card_response_info:
            await card_image.evaluate("(image, path) => { image.src = path; }", CARD_404_PATH)
        card_response = await card_response_info.value
        if card_response.status != 404:
            fail("Kompetitor card fallback: URL uji wajib benar-benar 404")
        card_fallback = comp_trigger.locator(".comp-thumb-missing")
        await card_fallback.wait_for(state="visible", timeout=5000)
        fallback_label = await card_fallback.evaluate("node => ({text: node.textContent.trim(), aria: node.getAttribute('aria-label')})")
        if "Foto gagal dimuat" not in (fallback_label["text"], fallback_label["aria"]):
            fail("Kompetitor card fallback: teks/aria gagal tidak tepat: " + json.dumps(fallback_label))

        async with page.expect_response(lambda response: response.url == modal_url) as modal_response_info:
            await page.evaluate("record => window.MTMSProductDetail.open(record)", {
                "model": "FALLBACK_E2E",
                "foto": MODAL_404_PATH,
            })
        modal_response = await modal_response_info.value
        if modal_response.status != 404:
            fail("Shared modal fallback: URL uji wajib benar-benar 404")
        modal = await wait_modal(page)
        modal_image = modal.locator(".pk-gal-img")
        handle = await modal_image.element_handle()
        await page.wait_for_function("""image =>
            image.getAttribute("src").startsWith("data:image/svg+xml") &&
            image.complete && image.naturalWidth > 0 && image.alt === "Foto gagal dimuat"
        """, arg=handle, timeout=5000)
        modal_fallback = await modal_image.evaluate("""image => ({
            src: image.getAttribute("src") || "",
            naturalWidth: image.naturalWidth,
            alt: image.alt
        })""")
        if not modal_fallback["src"].startswith("data:image/svg+xml") or modal_fallback["naturalWidth"] <= 0 or modal_fallback["alt"] != "Foto gagal dimuat":
            fail("Shared modal fallback: state gambar tidak tepat: " + json.dumps(modal_fallback))
    finally:
        await page.evaluate("() => window.MTMSProductDetail && window.MTMSProductDetail.close()")
        await page.reload(wait_until="networkidle")


async def assert_mobile_body_lock(page, record):
    original_style = await page.evaluate("document.body.getAttribute('style')")
    before = await page.evaluate("""() => {
        const body = document.body;
        const spacer = document.createElement("div");
        spacer.id = "mtms-body-lock-verifier-spacer";
        spacer.style.height = "1200px";
        spacer.setAttribute("aria-hidden", "true");
        body.appendChild(spacer);
        body.style.setProperty("position", "relative");
        body.style.setProperty("top", "7px");
        body.style.setProperty("width", "98%");
        body.style.setProperty("overflow", "visible");
        const maxScroll = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        window.scrollTo({top: Math.min(240, maxScroll), left: 0, behavior: "instant"});
        const properties = ["position", "top", "width", "overflow"];
        return {
            scrollY: window.scrollY,
            styles: Object.fromEntries(properties.map(property => [property, {
                value: body.style.getPropertyValue(property),
                priority: body.style.getPropertyPriority(property)
            }]))
        };
    }""")
    if before["scrollY"] < 32:
        fail("Produk 390px: fixture tidak cukup panjang untuk membuktikan pemulihan scroll non-zero")

    opening_scroll = await page.evaluate("""record => {
        const scrollY = window.scrollY;
        window.MTMSProductDetail.open(record);
        return scrollY;
    }""", record)
    if opening_scroll < 32:
        fail("Produk 390px: scroll aktual saat open harus tetap non-zero")
    modal = await wait_modal(page)
    locked = await page.evaluate("""() => ({
        scrollHeight: document.documentElement.scrollHeight,
        clientHeight: document.documentElement.clientHeight,
        position: document.body.style.position,
        top: document.body.style.top,
        width: document.body.style.width,
        overflow: document.body.style.overflow
    })""")
    if locked["scrollHeight"] > locked["clientHeight"] + 1:
        fail("Produk 390px: document masih menjadi jalur scroll kedua saat modal terbuka: " + json.dumps(locked))
    if locked["position"] != "fixed" or locked["width"] != "100%" or locked["overflow"] != "hidden":
        fail("Produk 390px: body lock tidak lengkap saat modal terbuka: " + json.dumps(locked))
    expected_top = "%spx" % -opening_scroll
    if locked["top"] != expected_top:
        fail("Produk 390px: body top tidak mengunci scroll aktual saat open; expected %s, got %s" % (expected_top, locked["top"]))

    await page.evaluate("record => window.MTMSProductDetail.open(record)", record)
    reopened = await page.evaluate("""() => ({
        position: document.body.style.position,
        top: document.body.style.top,
        width: document.body.style.width,
        overflow: document.body.style.overflow
    })""")
    expected_locked = {key: locked[key] for key in ("position", "top", "width", "overflow")}
    if reopened != expected_locked:
        fail("Produk 390px: open kedua menyimpan atau mereset body lock: " + json.dumps(reopened))

    await page.keyboard.press("Escape")
    await modal.wait_for(state="hidden")
    await page.wait_for_function("expected => Math.abs(window.scrollY - expected) <= 1", arg=opening_scroll, timeout=3000)
    restored = await page.evaluate("""() => {
        const body = document.body;
        const properties = ["position", "top", "width", "overflow"];
        return {
            scrollY: window.scrollY,
            styles: Object.fromEntries(properties.map(property => [property, {
                value: body.style.getPropertyValue(property),
                priority: body.style.getPropertyPriority(property)
            }]))
        };
    }""")
    if restored["styles"] != before["styles"]:
        fail("Produk 390px: inline style body tidak pulih persis: " + json.dumps(restored))
    if abs(restored["scrollY"] - opening_scroll) > 1:
        fail("Produk 390px: posisi scroll tidak pulih: " + json.dumps(restored))

    await page.evaluate("""style => {
        document.getElementById("mtms-body-lock-verifier-spacer").remove();
        if (style === null) document.body.removeAttribute("style");
        else document.body.setAttribute("style", style);
    }""", original_style)


async def assert_embedded_first_render(browser, base):
    async def delayed_api(route):
        await asyncio.sleep(4)
        await route.continue_()

    page = await browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("console", lambda msg: errors.append("console-" + msg.type + ": " + msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append("pageerror: " + str(err)))
    await page.route("**/api/produk", delayed_api)
    await page.route("**/api/kompetitor", delayed_api)
    started = asyncio.get_running_loop().time()
    await page.goto(base + "/kompetitor.html", wait_until="domcontentloaded")
    await page.locator(".comp-detail-trigger").first.wait_for(state="visible", timeout=5000)
    elapsed = asyncio.get_running_loop().time() - started
    if elapsed >= 1.2:
        fail("Kompetitor: render data bawaan terlalu lambat %.3fs; errors=%s" % (elapsed, json.dumps(errors)))
    if await page.evaluate("window.MTMS_COMPETITOR_LIVE_READY !== false"):
        fail("Kompetitor: fixture API tertunda tidak membuktikan render sebelum API")
    await page.wait_for_function("window.MTMS_COMPETITOR_LIVE_READY === true", timeout=10000)
    if await page.locator(".comp-edit:enabled").count() == 0:
        fail("Kompetitor: tombol edit tidak aktif sesudah data live selesai")
    await page.close()

    page = await browser.new_page(viewport={"width": 1440, "height": 900})
    await page.route("**/api/produk", delayed_api)
    await page.route("**/api/foto", delayed_api)
    started = asyncio.get_running_loop().time()
    await page.goto(base + "/produk.html", wait_until="domcontentloaded")
    await page.locator(".pk-card").first.wait_for(state="visible", timeout=5000)
    elapsed = asyncio.get_running_loop().time() - started
    if elapsed >= 1.2:
        fail("Produk: render data bawaan terlalu lambat %.3fs" % elapsed)
    if await page.locator(".pk-edit-add").count():
        fail("Produk: editor aktif sebelum data live selesai")
    await page.wait_for_function("window.MTMS_DATA_LIVE === true", timeout=12000)
    await page.locator(".pk-edit-add").wait_for(state="visible", timeout=2000)
    await page.close()


async def assert_visual_round_3(modal, width):
    text = await modal.inner_text()
    if PRICE_SOURCE_DISPLAY not in text:
        fail("Kompetitor brand: source harga manusia tidak tampil: " + PRICE_SOURCE_DISPLAY)
    if PRICE_SOURCE_RAW in text:
        fail("Kompetitor brand: source harga mentah masih tampil di modal fixture")

    missing_rows = modal.locator("table tbody tr.pk-detail-missing")
    if await missing_rows.count() != 1:
        fail("Kompetitor brand: missing wajib diringkas tepat satu row")
    missing_font_styles = await missing_rows.evaluate_all(
        "rows => rows.map(row => getComputedStyle(row).fontStyle)"
    )
    if any(style != "normal" for style in missing_font_styles):
        fail("Kompetitor brand: missing wajib memakai font-style normal: " + json.dumps(missing_font_styles))
    missing_text = await missing_rows.inner_text()
    expected_missing = [
        "Rentang kapasitas",
        "Material pintu",
        "Daya listrik",
        "Garansi kompresor",
        "Warna / varian",
        "Seri",
    ]
    if "Belum tersedia" not in missing_text:
        fail("Kompetitor brand: row ringkasan missing tidak berteks Belum tersedia")
    absent_labels = [label for label in expected_missing if label not in missing_text]
    if absent_labels:
        fail("Kompetitor brand: row ringkasan tidak menyebut semua field kosong: " + ", ".join(absent_labels))

    normal_labels = await modal.locator("table tbody tr:not(.pk-detail-missing) th").all_inner_texts()
    forbidden_rows = [label for label in expected_missing + ["Kategori", "Harga pasar"] if label in normal_labels]
    if forbidden_rows:
        fail("Kompetitor brand: field kosong/kategori/harga masih menjadi row biasa: " + ", ".join(forbidden_rows))

    order = await modal.evaluate("""root => {
        const price = root.querySelector(".pk-price-hero");
        const table = root.querySelector("table");
        const headings = Array.from(root.querySelectorAll("h4"));
        const sourceHeadings = headings.filter(node => node.textContent.trim() === "Sumber data");
        const sourceContainers = Array.from(root.querySelectorAll(".pk-detail-source"));
        const sourceHeading = sourceHeadings[0];
        const source = sourceContainers[0];
        const feature = headings.find(node => node.textContent.trim() === "Fitur Unggulan");
        const sourceLinks = source ? Array.from(source.querySelectorAll("a")) : [];
        return {
            sourceHeadingCount: sourceHeadings.length,
            sourceContainerCount: sourceContainers.length,
            sourceImmediatelyAfterPrice: !!price && price.nextElementSibling === sourceHeading &&
                sourceHeading.nextElementSibling === source,
            featureImmediatelyAfterSource: !!source && source.nextElementSibling === feature,
            sourceLinkCount: sourceLinks.length,
            everySourceLinkBeforeFeature: !!feature && sourceLinks.length > 0 && sourceLinks.every(link =>
                !!(link.compareDocumentPosition(feature) & Node.DOCUMENT_POSITION_FOLLOWING)),
            featureBeforeTable: !!feature && !!table &&
                !!(feature.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING),
            benefitHeadingCount: headings
                .filter(node => node.textContent.trim() === "Keunggulan & Fitur").length
        };
    }""")
    if order["sourceHeadingCount"] != 1 or order["sourceContainerCount"] != 1:
        fail("Kompetitor brand: Sumber data wajib punya tepat satu heading dan container: " + json.dumps(order))
    if not order["sourceImmediatelyAfterPrice"] or not order["featureImmediatelyAfterSource"]:
        fail("Kompetitor brand: urutan wajib harga, Sumber data, link sumber, lalu Fitur Unggulan: " + json.dumps(order))
    if not order["sourceLinkCount"] or not order["everySourceLinkBeforeFeature"]:
        fail("Kompetitor brand: link sumber wajib berada sebelum Fitur Unggulan: " + json.dumps(order))
    if not order["featureBeforeTable"]:
        fail("Kompetitor brand: Fitur Unggulan wajib tetap sebelum tabel")
    if order["benefitHeadingCount"]:
        fail("Kompetitor brand: heading Keunggulan & Fitur tampil saat benefit kosong")

    if width == 390:
        capacity_metrics = await modal.evaluate("""root => {
            const labels = Array.from(root.querySelectorAll(".pk-modal-right table th"));
            const label = labels.find(node => node.textContent.trim() === "Kapasitas");
            if (!label) return null;
            const value = label.nextElementSibling;
            const row = label.parentElement;
            const labelRect = label.getBoundingClientRect();
            const valueRect = value.getBoundingClientRect();
            const rowRect = row.getBoundingClientRect();
            return {
                rowDisplay: getComputedStyle(row).display,
                labelDisplay: getComputedStyle(label).display,
                valueDisplay: getComputedStyle(value).display,
                labelWhiteSpace: getComputedStyle(label).whiteSpace,
                labelWidth: labelRect.width,
                rowWidth: rowRect.width,
                labelScrollWidth: label.scrollWidth,
                labelClientWidth: label.clientWidth,
                labelBottom: labelRect.bottom,
                valueTop: valueRect.top
            };
        }""")
        if not capacity_metrics:
            fail("Kompetitor 390px: label Kapasitas tidak ditemukan")
        if any(capacity_metrics[key] != "block" for key in ("rowDisplay", "labelDisplay", "valueDisplay")):
            fail("Kompetitor 390px: row spesifikasi wajib satu kolom label di atas nilai: " + json.dumps(capacity_metrics))
        if capacity_metrics["labelWhiteSpace"] != "nowrap":
            fail("Kompetitor 390px: label Kapasitas masih boleh pecah kata: " + json.dumps(capacity_metrics))
        if capacity_metrics["labelScrollWidth"] > capacity_metrics["labelClientWidth"] + 1:
            fail("Kompetitor 390px: lebar label Kapasitas tidak memadai: " + json.dumps(capacity_metrics))
        if capacity_metrics["labelWidth"] < capacity_metrics["rowWidth"] - 1 or capacity_metrics["labelBottom"] > capacity_metrics["valueTop"] + 1:
            fail("Kompetitor 390px: label Kapasitas belum berada penuh di atas nilai: " + json.dumps(capacity_metrics))

        close_metrics = await modal.locator(".pk-modal-close").evaluate("""button => {
            const rect = button.getBoundingClientRect();
            const style = getComputedStyle(button);
            return {
                width: rect.width,
                height: rect.height,
                visible: style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0
            };
        }""")
        if not close_metrics["visible"] or close_metrics["width"] < 44 or close_metrics["height"] < 44:
            fail("Kompetitor 390px: pk-modal-close wajib terlihat dan minimal 44x44: " + json.dumps(close_metrics))


async def run_browser(base, aqua, competitor, competitor_brand):
    async with async_playwright() as pw:
        launch = {"headless": True}
        if os.path.exists(CHROME):
            launch["executable_path"] = CHROME
        browser = await pw.chromium.launch(**launch)
        await assert_embedded_first_render(browser, base)
        for width, height in ((1440, 900), (390, 844)):
            page = await browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on("console", lambda msg, bag=errors: bag.append("console-" + msg.type + ": " + msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err, bag=errors: bag.append("pageerror: " + str(err)))

            await page.goto(base + "/produk.html?model=" + aqua["model"], wait_until="networkidle")
            if not await page.evaluate("!!(window.MTMSProductDetail && typeof window.MTMSProductDetail.open === 'function')"):
                fail("Produk: singleton window.MTMSProductDetail.open belum tersedia")
            modal = await wait_modal(page)
            if "CANONICAL_SENTINEL_FROM_PRODUCT_API" not in await modal.inner_text():
                fail("Produk card: shared modal tidak memakai record API canonical")
            await page.keyboard.press("Escape")
            await modal.wait_for(state="hidden")
            restored = await page.evaluate("document.body.style.overflow")
            if restored:
                fail("Produk modal: body scroll tidak dipulihkan sesudah Escape")
            if width == 390:
                await assert_mobile_body_lock(page, aqua)
            await assert_clean(page, errors, "produk %dpx" % width)
            await page.close()

            page = await browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on("console", lambda msg, bag=errors: bag.append("console-" + msg.type + ": " + msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err, bag=errors: bag.append("pageerror: " + str(err)))
            await page.goto(base + "/produk.html?model=" + aqua["model"], wait_until="networkidle")
            modal = await wait_modal(page)
            if aqua["model"] not in await modal.inner_text():
                fail("Produk ?model=: exact model tidak auto-open")
            await page.close()

            page = await browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on("console", lambda msg, bag=errors: bag.append("console-" + msg.type + ": " + msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err, bag=errors: bag.append("pageerror: " + str(err)))
            await page.goto(base + "/kompetitor.html", wait_until="networkidle")
            aqua_trigger = page.locator('.comp-detail-trigger[data-brand="AQUA"][data-model="%s"]' % aqua["model"])
            await aqua_trigger.wait_for(state="visible", timeout=5000)

            edit = page.locator('.comp-edit[data-brand="AQUA"][data-model="%s"]' % aqua["model"])
            await edit.click()
            if await page.locator('.pk-modal.open[data-mtms-product-detail="true"]').count():
                fail("Kompetitor Edit: klik Edit ikut membuka shared detail")
            await page.locator("#cef_cancel").click()

            await aqua_trigger.focus()
            await page.keyboard.press("Enter")
            modal = await wait_modal(page)
            text = await modal.inner_text()
            if "CANONICAL_SENTINEL_FROM_PRODUCT_API" not in text or "CANONICAL_MATERIAL_SENTINEL" not in text:
                fail("Kompetitor AQUA: bukan record katalog Produk canonical")
            if "Rp 3.260.000" not in text:
                fail("Kompetitor AQUA: harga kosong di canonical tidak diperkaya dari record kompetitor")
            if not await modal.locator('img[src="%s"]' % aqua["image"]).count():
                fail("Kompetitor AQUA: foto kosong di canonical tidak diperkaya dari record kompetitor")
            if await modal.locator("h4", has_text="Keunggulan & Fitur").count():
                fail("Kompetitor AQUA: benefit yang identik dengan fitur masih dirender dua kali")
            link = modal.locator('a[href*="produk.html?model="]')
            if not await link.count():
                fail("Kompetitor AQUA: canonicalUrl ke produk.html?model= belum ada")
            await page.keyboard.press("Escape")

            comp_trigger = page.locator('.comp-detail-trigger[data-brand="%s"][data-model="%s"]' % (competitor_brand, competitor["model"]))
            await comp_trigger.scroll_into_view_if_needed()
            await assert_local_loaded_image(page, comp_trigger.locator("img.comp-thumb"), "Kompetitor card")
            await comp_trigger.focus()
            await page.keyboard.press("Space")
            modal = await wait_modal(page)
            text = await modal.inner_text()
            if competitor_brand not in text:
                fail("Kompetitor brand: brand tidak tampil di modal bersama")
            if competitor["fitur"][0] not in text:
                fail("Kompetitor brand: fitur embedded tidak memperkaya response API")
            if not await modal.locator('a[href="%s"]' % competitor["source_url"]).count():
                fail("Kompetitor brand: source URL berbukti tidak tampil")
            if not await modal.locator('img[src="%s"]' % competitor["image"]).count():
                fail("Kompetitor brand: foto resmi berbukti tidak tampil")
            await assert_local_loaded_image(page, modal.locator("img.pk-modal-img").first, "Kompetitor modal")
            photo_source_link = modal.locator('a[href="%s"]' % competitor["photo_url"])
            if not await photo_source_link.count():
                fail("Kompetitor brand: provenance photo_url resmi tidak tampil")
            photo_source_labels = [label.strip() for label in await photo_source_link.all_inner_texts()]
            if "Sumber foto" not in photo_source_labels:
                fail("Kompetitor brand: label Sumber foto tidak tampil: " + json.dumps(photo_source_labels))
            if "Sumber foto resmi" in text:
                fail("Kompetitor brand: label lama Sumber foto resmi masih tampil")
            if "Belum tersedia" not in text:
                fail("Kompetitor brand: field kosong tidak dilabel Belum tersedia")
            await assert_visual_round_3(modal, width)
            await page.keyboard.press("Escape")
            await assert_clean(page, errors, "kompetitor %dpx" % width)
            await assert_real_image_fallbacks(page, base, comp_trigger)
            await page.close()
        await browser.close()


async def main():
    catalog, api_comp, aqua, competitor, competitor_brand = fixtures()
    Handler.catalog = catalog
    Handler.competitor = api_comp
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=SITE))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        await run_browser("http://127.0.0.1:%d" % server.server_port, aqua, competitor, competitor_brand)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    print("PASS verify_product_detail: embedded-first <1.2s with API delayed 4s, shared modal, canonical AQUA fallback enrichment, duplicate feature suppression, real 404 image fallbacks, edit isolation, keyboard, body-lock, 1440/390")


if __name__ == "__main__":
    asyncio.run(main())
