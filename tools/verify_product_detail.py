# -*- coding: utf-8 -*-
"""Gerbang E2E komponen detail produk bersama. Read-only terhadap API/data."""
import asyncio
import copy
import json
import os
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.async_api import async_playwright


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
CATALOG_PATH = os.path.join(SITE, "data", "produk-katalog.json")
COMP_PATH = os.path.join(SITE, "data", "kompetitor.json")
CATEGORIES_PATH = os.path.join(SITE, "data", "spec-categories.json")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PRICE_SOURCE_RAW = "price_gfk (brief)"
PRICE_SOURCE_DISPLAY = "price GfK (ringkasan riset)"
CARD_404_PATH = "/__verify_product_detail__/missing-card.png"
MODAL_404_PATH = "/__verify_product_detail__/missing-modal.png"
FIXTURE_SHA = "ticket04-fixture-sha"
LIVE_CATEGORY_KEY = "live_fixture_extra"
LIVE_CATEGORY_LABEL = "Kategori Live Fixture"
LIVE_CATEGORY_VALUE = "LIVE_CATEGORY_VALUE_FROM_REFRESH"
ADDITIONAL_KEY = "official_features"
FIXTURE_VERIFIED_AT = "2026-08-21T10:11:12+07:00"
FIXTURE_SOURCE_KIND = "official_product_page"
SAFE_SAME_ORIGIN_SOURCE = "/__verify_product_detail__/same-origin-source"
SAFE_SAME_ORIGIN_SUGGESTION = "/__verify_product_detail__/same-origin-suggestion"
UNSAFE_PROTOCOL_RELATIVE = "//evil.example/ticket04-protocol-relative"
UNSAFE_JAVASCRIPT = "javascript:window.__ticket04_unsafe=1"
UNSAFE_BACKSLASH = "https:\\evil.example\\ticket04-backslash"
UNSAFE_CONTROL = "https://evil.example/ticket04\ncontrol"
THEME_SETTLE_MS = 350
RESEARCH_SUGGESTION_ID = "b" * 64
RESEARCH_CANDIDATE_KEY = "compressor_type"
RESEARCH_CANDIDATE_VALUE = "Inverter Cepat Fixture"


def research_job_public(job):
    return {
        "job_id": job["job_id"],
        "model_id": job["model_id"],
        "target": "kompetitor",
        "status": job["status"],
        "requested_at": job["requested_at"],
        "started_at": None,
        "finished_at": "2026-08-21T15:00:00+00:00",
        "error_code": None,
        "candidates": job["candidates"],
    }


def fail(message):
    raise AssertionError(message)


async def install_listener_probe(page):
    await page.add_init_script("""() => {
        const originalAdd = EventTarget.prototype.addEventListener;
        const originalRemove = EventTarget.prototype.removeEventListener;
        const scrollListeners = new WeakMap();
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (type === "scroll" && this instanceof Element && this.classList.contains("pk-modal-box")) {
                if (!scrollListeners.has(this)) scrollListeners.set(this, new Set());
                scrollListeners.get(this).add(listener);
            }
            return originalAdd.call(this, type, listener, options);
        };
        EventTarget.prototype.removeEventListener = function(type, listener, options) {
            if (type === "scroll" && scrollListeners.has(this)) scrollListeners.get(this).delete(listener);
            return originalRemove.call(this, type, listener, options);
        };
        window.__mtmsScrollListenerCount = node => scrollListeners.has(node) ? scrollListeners.get(node).size : 0;
    }""")


def is_local_competitor_fixture(row):
    image = str(row.get("image") or "").replace("\\", "/")
    photo_url = str(row.get("photo_url") or "")
    if not image.startswith("assets/kompetitor/") or not photo_url.startswith(("http://", "https://")):
        return False
    local_path = os.path.normpath(os.path.join(SITE, image.replace("/", os.sep)))
    assets_root = os.path.normpath(os.path.join(SITE, "assets", "kompetitor"))
    return os.path.commonpath((local_path, assets_root)) == assets_root and os.path.isfile(local_path)


def spec_entry(value, prefix, key):
    return {
        "value": value,
        "source_url": "https://fixture.example/%s/%s" % (prefix.lower(), key),
        "source_kind": FIXTURE_SOURCE_KIND,
        "verified_at": FIXTURE_VERIFIED_AT,
        "origin": "research",
        "user_locked": False,
    }


def fixture_spec_values(prefix):
    values = {
        "form_factor": prefix + " FORM FACTOR",
        "door_count": 3,
        "freezer_position": "Atas",
        "gross_capacity_l": 777,
        "width_mm": 901,
        "height_mm": 1802,
        "rated_power_w": "88 W",
        "compressor_type": "Twin Inverter",
        "cooling_system": ["Fan Cooling", "Direct Cooling"],
        "defrost_type": False,
        ADDITIONAL_KEY: [prefix + " LIST A", prefix + " LIST B"],
        "wifi": True,
        LIVE_CATEGORY_KEY: LIVE_CATEGORY_VALUE,
    }
    result = {key: spec_entry(value, prefix, key) for key, value in values.items()}
    result["compressor_type"]["source_url"] = SAFE_SAME_ORIGIN_SOURCE
    result["wifi"]["source_url"] = UNSAFE_PROTOCOL_RELATIVE
    result["defrost_type"]["source_url"] = UNSAFE_JAVASCRIPT
    result["door_count"]["origin"] = "user"
    result["door_count"]["user_locked"] = True
    result["gross_capacity_l"]["origin"] = "legacy"
    result["height_mm"]["origin"] = "unknown"
    return result


def fixture_suggestions(prefix):
    return [
        {
            "key": "form_factor",
            "value": prefix + " PENDING VALUE",
            "source_url": "https://fixture.example/%s/pending" % prefix.lower(),
            "source_kind": FIXTURE_SOURCE_KIND,
            "verified_at": FIXTURE_VERIFIED_AT,
            "origin": "research",
            "status": "pending",
        },
        {
            "key": "door_count",
            "value": 4,
            "source_url": SAFE_SAME_ORIGIN_SUGGESTION,
            "source_kind": FIXTURE_SOURCE_KIND,
            "verified_at": FIXTURE_VERIFIED_AT,
            "origin": "research",
            "status": "accepted",
        },
        {
            "key": "width_mm",
            "value": 999,
            "source_url": UNSAFE_JAVASCRIPT,
            "source_kind": "unsafe_fixture",
            "verified_at": FIXTURE_VERIFIED_AT,
            "origin": "research",
            "status": "rejected",
        },
        {
            "key": "height_mm",
            "value": 1999,
            "source_url": UNSAFE_PROTOCOL_RELATIVE,
            "source_kind": "unsafe_fixture",
            "verified_at": FIXTURE_VERIFIED_AT,
            "origin": "research",
            "status": "rejected",
        },
        {
            "key": "gross_capacity_l",
            "value": 2999,
            "source_url": UNSAFE_BACKSLASH,
            "source_kind": "unsafe_fixture",
            "verified_at": FIXTURE_VERIFIED_AT,
            "origin": "research",
            "status": "rejected",
        },
        {
            "key": "rated_power_w",
            "value": 3999,
            "source_url": UNSAFE_CONTROL,
            "source_kind": "unsafe_fixture",
            "verified_at": FIXTURE_VERIFIED_AT,
            "origin": "research",
            "status": "rejected",
        },
    ]


def fixture_feature_meta(prefix):
    return {
        "source_url": "https://fixture.example/%s/features" % prefix.lower(),
        "source_kind": FIXTURE_SOURCE_KIND,
        "verified_at": FIXTURE_VERIFIED_AT,
        "origin": "research",
        "user_locked": False,
    }


def fixtures():
    with open(CATALOG_PATH, encoding="utf-8") as fh:
        catalog = json.load(fh)
    with open(COMP_PATH, encoding="utf-8") as fh:
        embedded_comp = json.load(fh)
    with open(CATEGORIES_PATH, encoding="utf-8") as fh:
        category_document = json.load(fh)
    if not embedded_comp.get("groups"):
        fail("Fixture gagal: data bawaan kompetitor tidak punya groups untuk render cepat")

    live_categories = copy.deepcopy(category_document)
    max_order = max(item["order"] for item in live_categories["spec_categories"])
    live_categories["spec_categories"].append({
        "key": LIVE_CATEGORY_KEY,
        "label": LIVE_CATEGORY_LABEL,
        "group": "Live Fixture",
        "unit": "-",
        "comparison": False,
        "order": max_order + 10,
        "active": True,
    })

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
    canonical_row["model_id"] = "AQUA::" + canonical_row["model"]
    canonical_row["foto"] = aqua["image"]
    canonical_row["foto_list"] = [aqua["image"], competitor["image"]]
    canonical_row["spec_values"] = fixture_spec_values("PRODUCT")
    canonical_row["research_suggestions"] = fixture_suggestions("PRODUCT")
    canonical_row["fitur_meta"] = fixture_feature_meta("PRODUCT")

    # API kompetitor sengaja tipis. Implementasi wajib memperkaya dari embedded,
    # tetapi groups API ini wajib tetap dipertahankan.
    api_comp = json.loads(json.dumps(embedded_comp))
    api_comp["groups"] = [{
        "aqua": aqua["model"],
        "competitors": {competitor_brand: competitor["model"]},
    }]
    for brand in api_comp["brands"]:
        for row in brand["models"]:
            if brand["brand"] == "AQUA" and row.get("model") == aqua["model"]:
                row["model_id"] = "AQUA::" + row["model"]
                row["spec_values"] = fixture_spec_values("AQUA_TABLE")
                row["research_suggestions"] = fixture_suggestions("AQUA_TABLE")
                row["fitur_meta"] = fixture_feature_meta("AQUA_TABLE")
            if brand["brand"] == competitor_brand and row.get("model") == competitor["model"]:
                row["fitur"] = []
                row["source_url"] = ""
                row["image"] = ""
                row["photo_url"] = ""
                row["price_source"] = ""
                row["model_id"] = competitor_brand + "::" + row["model"]
                row["spec_values"] = fixture_spec_values("COMPETITOR")
                row["research_suggestions"] = fixture_suggestions("COMPETITOR")
                row["fitur_meta"] = fixture_feature_meta("COMPETITOR")
    competitor_fixture = next(
        row for brand in api_comp["brands"] if brand["brand"] == competitor_brand
        for row in brand["models"] if row["model"] == competitor["model"]
    )
    return {
        "catalog": canonical,
        "competitor_document": api_comp,
        "categories": live_categories,
        "aqua": aqua,
        "canonical_row": canonical_row,
        "competitor": competitor,
        "competitor_fixture": competitor_fixture,
        "competitor_brand": competitor_brand,
    }


class Handler(SimpleHTTPRequestHandler):
    catalog = None
    competitor = None
    categories = None
    research = None

    def log_message(self, *_args):
        pass

    def _json(self, payload, status=200, headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _research_log(self, entry):
        if self.research is not None:
            self.research["log"].append(entry)

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/api/research":
            self._research_log({"method": "GET", "path": self.path})
            params = dict(part.split("=", 1) for part in query.split("&") if "=" in part)
            job = self.research["jobs"].get(params.get("job_id")) if self.research else None
            if not job:
                return self._json({"error": "job tidak ditemukan"}, 404)
            return self._json(research_job_public(job), 200, {"Cache-Control": "no-store"})
        path = self.path.split("?", 1)[0]
        if path in (CARD_404_PATH, MODAL_404_PATH):
            self.send_error(404)
            return
        if path == "/api/produk":
            self._research_log({"method": "GET", "path": "/api/produk"})
            return self._json(self.catalog, headers={"X-Data-SHA": FIXTURE_SHA, "ETag": '"%s"' % FIXTURE_SHA})
        if path == "/api/kompetitor":
            self._research_log({"method": "GET", "path": "/api/kompetitor"})
            return self._json(self.competitor, headers={"X-Data-SHA": FIXTURE_SHA, "ETag": '"%s"' % FIXTURE_SHA})
        if path == "/api/spec-categories":
            return self._json(self.categories, headers={"X-Data-SHA": FIXTURE_SHA, "ETag": '"%s"' % FIXTURE_SHA})
        if path == "/api/foto":
            return self._json({"files": []})
        return super().do_GET()

    def do_PUT(self):
        return self._json({"error": "checker read-only: PUT dilarang"}, 405)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/research":
            if not self.research:
                return self._json({"error": "checker research disabled"}, 404)
            body = self._read_body()
            self._research_log({"method": "POST", "body": body})
            if not isinstance(body, dict) or set(body) != {"model_id"} or not isinstance(body["model_id"], str):
                return self._json({"error": "invalid input: exact model_id only"}, 400)
            counter = self.research["counter"] + 1
            self.research["counter"] = counter
            job_id = "%032x" % counter
            job = {
                "job_id": job_id,
                "model_id": body["model_id"],
                "status": "completed",
                "requested_at": "2026-08-21T14:59:59+00:00",
                "candidates": [{
                    "key": RESEARCH_CANDIDATE_KEY,
                    "value": RESEARCH_CANDIDATE_VALUE,
                    "observed_value": None,
                    "source_url": "https://fixture.example/research",
                    "source_kind": FIXTURE_SOURCE_KIND,
                    "verified_at": "2026-08-21T15:00:00+00:00",
                    "status": "pending",
                    "suggestion_id": RESEARCH_SUGGESTION_ID,
                }],
            }
            self.research["jobs"][job_id] = job
            return self._json({"job_id": job_id, "status": "queued", "poll_after_ms": 50}, 202)
        return self._json({"error": "checker read-only: POST dilarang"}, 405)

    def do_PATCH(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/kompetitor":
            if not self.research:
                return self._json({"error": "checker disabled"}, 404)
            body = self._read_body()
            self._research_log({"method": "PATCH", "path": "/api/kompetitor", "body": body,
                                "if_match": self.headers.get("If-Match") or ""})
            if (not isinstance(body, dict) or
                    body.get("action") not in ("set_spec_value", "accept_suggestion", "reject_suggestion",
                                               "accept_feature_suggestion", "reject_feature_suggestion") or
                    not isinstance(body.get("model_id"), str) or
                    (body.get("action") == "set_spec_value" and not isinstance(body.get("key"), str)) or
                    (body.get("action") != "set_spec_value" and not isinstance(body.get("suggestion_index"), int))):
                return self._json({"error": "invalid mutation"}, 400)
            if (self.headers.get("If-Match") or "") != '"' + FIXTURE_SHA + '"':
                return self._json({"error": "base SHA / If-Match tidak cocok"}, 412)
            return self._json({"ok": True, "sha": FIXTURE_SHA, "model": {"ok": True}}, 200)
        if path == "/api/research":
            if not self.research:
                return self._json({"error": "checker research disabled"}, 404)
            body = self._read_body()
            self._research_log({
                "method": "PATCH",
                "body": body,
                "if_match": self.headers.get("If-Match") or "",
            })
            if (not isinstance(body, dict) or set(body) != {"action", "job_id", "suggestion_id"} or
                    body.get("action") not in ("accept", "reject")):
                return self._json({"error": "invalid decision input"}, 400)
            job = self.research["jobs"].get(body.get("job_id")) if self.research else None
            if not job:
                return self._json({"error": "job tidak ditemukan"}, 404)
            candidate = next((item for item in job["candidates"]
                              if item.get("suggestion_id") == body.get("suggestion_id")), None)
            if not candidate:
                return self._json({"error": "suggestion tidak ditemukan"}, 404)
            if candidate["status"] == "accepted" and body["action"] == "accept":
                return self._json(research_job_public(job), 200)
            if candidate["status"] == "rejected" and body["action"] == "reject":
                return self._json(research_job_public(job), 200)
            if candidate["status"] != "pending":
                return self._json({"error": "suggestion sudah diputus"}, 409)
            if body["action"] == "accept":
                expected = '"' + FIXTURE_SHA + '"'
                if (self.headers.get("If-Match") or "") != expected:
                    return self._json({"error": "base SHA / If-Match tidak cocok"}, 412)
                candidate["status"] = "accepted"
            else:
                candidate["status"] = "rejected"
            return self._json(research_job_public(job), 200)
        return self._json({"error": "checker read-only: PATCH dilarang"}, 405)

    def do_DELETE(self):
        return self._json({"error": "checker read-only: DELETE dilarang"}, 405)


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


def active_categories(category_document, comparison=None):
    rows = [row for row in category_document["spec_categories"] if row.get("active") is True]
    if comparison is not None:
        rows = [row for row in rows if row.get("comparison") is comparison]
    return sorted(rows, key=lambda row: (row["order"], row["key"]))


def has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(has_value(item) for item in value)
    return True


def scalar_text(value):
    if isinstance(value, bool):
        return "Ya" if value else "Tidak"
    if isinstance(value, (str, int, float)) and not isinstance(value, complex):
        return str(value)
    return ""


def expected_spec_text(entry, category):
    if not isinstance(entry, dict) or not has_value(entry.get("value")):
        return "Belum tersedia"
    value = entry.get("value")
    if isinstance(value, list):
        text = ", ".join(filter(None, (scalar_text(item) for item in value)))
    else:
        text = scalar_text(value)
    if not text:
        return "Belum tersedia"
    unit = str(category.get("unit") or "").strip()
    if unit and unit != "-":
        pattern = r"(^|[\s(,/])%s(?=$|[\s),/])" % re.escape(unit)
        if not re.search(pattern, text, flags=re.IGNORECASE):
            text += " " + unit
    return text


async def assert_tap_targets(page, label):
    undersized = await page.evaluate("""() => Array.from(document.querySelectorAll("button, select"))
        .map(node => {
            const rect = node.getBoundingClientRect();
            const style = getComputedStyle(node);
            return {node, rect, style};
        })
        .filter(item => item.rect.width > 0 && item.rect.height > 0 &&
            item.style.display !== "none" && item.style.visibility !== "hidden")
        .filter(item => item.rect.width < 44 || item.rect.height < 44)
        .map(item => ({
            tag: item.node.tagName,
            className: item.node.className,
            text: (item.node.textContent || item.node.getAttribute("aria-label") || "").trim().slice(0, 50),
            width: item.rect.width,
            height: item.rect.height
        }))""")
    if undersized:
        fail(label + ": kontrol di bawah 44x44: " + json.dumps(undersized, ensure_ascii=False))


async def assert_min_font_size(locator, minimum, label):
    sizes = await locator.evaluate_all("nodes => nodes.map(node => ({text: (node.textContent || '').trim().slice(0, 60), fontSize: parseFloat(getComputedStyle(node).fontSize)}))")
    if not sizes:
        fail(label + ": fixture font kosong")
    undersized = [item for item in sizes if item["fontSize"] + 0.01 < minimum]
    if undersized:
        fail(label + ": computed fontSize di bawah %.1fpx: %s" % (minimum, json.dumps(undersized, ensure_ascii=False)))


async def assert_modal_scroll_path(modal, label):
    state = await modal.evaluate("""root => {
        const box = root.querySelector(".pk-modal-box");
        const cue = root.querySelector(".pk-detail-cue");
        const cueStyle = cue ? getComputedStyle(cue) : null;
        const scrollbarStyle = getComputedStyle(box, "::-webkit-scrollbar");
        const nestedScrollers = Array.from(box.querySelectorAll("*")).filter(node => {
            const style = getComputedStyle(node);
            return (style.overflowY === "auto" || style.overflowY === "scroll") &&
                node.scrollHeight > node.clientHeight + 1;
        }).map(node => node.className || node.tagName);
        return {
            documentScroll: document.documentElement.scrollHeight > document.documentElement.clientHeight + 1,
            overlayOverflowY: getComputedStyle(root).overflowY,
            boxOverflowY: getComputedStyle(box).overflowY,
            boxClientHeight: box.clientHeight,
            boxScrollHeight: box.scrollHeight,
            scrollbarColor: getComputedStyle(box).scrollbarColor,
            webkitScrollbarWidth: scrollbarStyle.width,
            nestedScrollers,
            cueText: cue ? cue.textContent.trim() : "",
            cueVisible: !!cue && cueStyle.display !== "none" && cueStyle.visibility !== "hidden" &&
                Number(cueStyle.opacity) > 0 && cue.getBoundingClientRect().height > 0
        };
    }""")
    if state["documentScroll"]:
        fail(label + ": modal membuka jalur scroll document kedua: " + json.dumps(state))
    if state["overlayOverflowY"] not in ("hidden", "clip") or state["boxOverflowY"] != "auto":
        fail(label + ": jalur scroll modal bukan satu box: " + json.dumps(state))
    if state["boxScrollHeight"] <= state["boxClientHeight"]:
        fail(label + ": fixture tidak cukup panjang untuk membuktikan scroll box tunggal: " + json.dumps(state))
    if state["nestedScrollers"]:
        fail(label + ": ada scrollbar kedua di dalam .pk-modal-box: " + json.dumps(state, ensure_ascii=False))
    try:
        scrollbar_width = float(str(state["webkitScrollbarWidth"]).replace("px", ""))
    except ValueError:
        scrollbar_width = 0
    if scrollbar_width < 8 or state["scrollbarColor"] in ("auto", ""):
        fail(label + ": scrollbar modal box belum jelas terlihat: " + json.dumps(state, ensure_ascii=False))
    if not state["cueVisible"] or "Detail berlanjut di bawah" not in state["cueText"]:
        fail(label + ": cue scroll modal tidak terlihat jelas: " + json.dumps(state, ensure_ascii=False))

    bottom = await modal.evaluate("""root => {
        const box = root.querySelector(".pk-modal-box");
        const marker = root.querySelector('[data-detail-bottom="true"]');
        box.scrollTop = box.scrollHeight;
        const boxRect = box.getBoundingClientRect();
        const markerRect = marker.getBoundingClientRect();
        return {
            reached: box.scrollTop + box.clientHeight >= box.scrollHeight - 1,
            markerVisible: markerRect.width > 0 && markerRect.height > 0 &&
                markerRect.top < boxRect.bottom + 1 && markerRect.bottom <= boxRect.bottom + 1,
            scrollTop: box.scrollTop,
            maxScroll: box.scrollHeight - box.clientHeight
        };
    }""")
    if not bottom["reached"] or not bottom["markerVisible"]:
        fail(label + ": bottom modal tidak benar-benar dapat dicapai: " + json.dumps(bottom))
    await modal.evaluate("""root => new Promise(resolve => {
        root.querySelector(".pk-modal-box").scrollTop = 0;
        requestAnimationFrame(() => requestAnimationFrame(resolve));
    })""")


async def assert_mobile_modal_image(modal, label):
    image = modal.locator(".pk-gal-img").first
    if await image.count() != 1:
        fail(label + ": gambar modal fixture tidak ada")
    image_metrics = await image.evaluate("""node => {
        const rect = node.getBoundingClientRect();
        return {height: rect.height, objectFit: getComputedStyle(node).objectFit};
    }""")
    if image_metrics["height"] < 170 or image_metrics["height"] > 190 or image_metrics["objectFit"] != "contain":
        fail(label + ": gambar mobile wajib sekitar 180px, <=190px, object-contain: " + json.dumps(image_metrics))
    stage = modal.locator(".pk-gal-stage")
    if await stage.count():
        stage_height = await stage.first.evaluate("node => node.getBoundingClientRect().height")
        if stage_height < 170 or stage_height > 190:
            fail(label + ": stage galeri mobile wajib sekitar 180px dan <=190px: %.2f" % stage_height)
        gallery = modal.locator(".pk-gal")
        before = await gallery.locator(".pk-gal-img").get_attribute("data-idx")
        await gallery.locator('.pk-gal-nav[data-dir="1"]').click()
        after = await gallery.locator(".pk-gal-img").get_attribute("data-idx")
        active = await gallery.locator(".pk-gal-thumb.active").get_attribute("data-idx")
        if before == after or active != after:
            fail(label + ": galeri tidak tetap berfungsi setelah stage dipadatkan")


async def assert_modal_round1(page, modal, record, width, label):
    expected_labels = ["Ringkasan", "Fitur", "Spesifikasi"]
    if record.get("research_suggestions"):
        expected_labels.append("Saran riset")
    actual_labels = await modal.locator(".pk-detail-nav button").all_inner_texts()
    if actual_labels != expected_labels:
        fail(label + ": nav section tidak exact/omit suggestion: %s != %s" % (actual_labels, expected_labels))
    nav_state = await modal.locator(".pk-detail-nav").evaluate("""nav => ({
        position: getComputedStyle(nav).position,
        cue: (nav.querySelector('.pk-detail-cue') || {}).textContent || ''
    })""")
    if nav_state["position"] != "sticky" or "Detail berlanjut di bawah" not in nav_state["cue"]:
        fail(label + ": nav tidak sticky atau cue lanjutan hilang: " + json.dumps(nav_state, ensure_ascii=False))

    async def assert_active_nav(expected, stage):
        state = await modal.locator(".pk-detail-nav button").evaluate_all("""buttons => buttons.map(button => ({
            label: button.textContent.trim(),
            active: button.classList.contains("is-active"),
            current: button.getAttribute("aria-current"),
            background: getComputedStyle(button).backgroundColor
        }))""")
        active = [item for item in state if item["active"] and item["current"] == "location"]
        if len(active) != 1 or active[0]["label"] != expected:
            fail(label + ": active nav %s bukan exact %s: %s" % (stage, expected, json.dumps(state, ensure_ascii=False)))
        inactive = next((item for item in state if item["label"] != expected), None)
        if inactive and inactive["background"] == active[0]["background"]:
            fail(label + ": active nav %s tidak berbeda visual" % stage)

    await assert_active_nav("Ringkasan", "awal")

    await assert_min_font_size(modal.locator(
        ".pk-detail-nav button, .pk-detail-cue, .pk-feature-provenance, .pk-feature-provenance *, "
        ".pk-spec-group h5, .pk-spec-row dt, .pk-spec-row dd, .pk-spec-missing, "
        ".pk-suggestion-head strong, .pk-suggestion-status, .pk-suggestion-value, "
        ".pk-suggestion-provenance, .pk-suggestion-provenance *"
    ), 12.8, label + " teks comparison/provenance/spec/suggestion")

    box = modal.locator(".pk-modal-box")
    box_handle = await box.element_handle()
    await box.evaluate("node => { node.scrollTop = 0; }")
    page_before = await page.evaluate("() => ({x: window.scrollX, y: window.scrollY, overlay: document.querySelector('.pk-modal').scrollTop})")
    await modal.get_by_role("button", name="Spesifikasi", exact=True).click()
    await assert_active_nav("Spesifikasi", "sesudah click")
    await page.wait_for_function("box => box.scrollTop > 40", arg=box_handle, timeout=2500)
    click_scroll = await box.evaluate("node => node.scrollTop")
    page_after_click = await page.evaluate("() => ({x: window.scrollX, y: window.scrollY, overlay: document.querySelector('.pk-modal').scrollTop})")
    if page_after_click != page_before:
        fail(label + ": click nav menggulir di luar .pk-modal-box: %s -> %s" % (page_before, page_after_click))

    summary_button = modal.get_by_role("button", name="Ringkasan", exact=True)
    await summary_button.focus()
    await page.keyboard.press("Enter")
    await assert_active_nav("Ringkasan", "sesudah keyboard")
    await page.wait_for_function("args => args.box.scrollTop < args.previous - 20", arg={"box": box_handle, "previous": click_scroll}, timeout=2500)
    page_after_keyboard = await page.evaluate("() => ({x: window.scrollX, y: window.scrollY, overlay: document.querySelector('.pk-modal').scrollTop})")
    if page_after_keyboard != page_before:
        fail(label + ": keyboard nav menggulir di luar .pk-modal-box: %s -> %s" % (page_before, page_after_keyboard))

    last_label = expected_labels[-1]
    await box.evaluate("node => { node.scrollTop = node.scrollHeight; }")
    await page.wait_for_function("""args => {
        const active = args.box.querySelector('.pk-detail-nav button[aria-current="location"]');
        return active && active.textContent.trim() === args.label;
    }""", arg={"box": box_handle, "label": last_label}, timeout=2500)
    await assert_active_nav(last_label, "scrollspy bottom")
    await box.evaluate("node => { node.scrollTop = 0; }")
    await page.wait_for_function("""box => {
        const active = box.querySelector('.pk-detail-nav button[aria-current="location"]');
        return active && active.textContent.trim() === 'Ringkasan';
    }""", arg=box_handle, timeout=2500)

    listener_count = await page.evaluate("""box => typeof window.__mtmsScrollListenerCount === "function" ?
        window.__mtmsScrollListenerCount(box) : 1""", box_handle)
    if listener_count != 1:
        fail(label + ": listener scrollspy menumpuk sesudah rerender/open: %s" % listener_count)

    fab = page.locator(".ds-editor-fab")
    if await fab.count():
        z_state = await page.evaluate("""() => ({
            modal: Number(getComputedStyle(document.querySelector('.pk-modal')).zIndex),
            trigger: Number(getComputedStyle(document.querySelector('.ds-editor-fab')).zIndex)
        })""")
        if z_state["modal"] <= z_state["trigger"]:
            fail(label + ": shared modal z-index tidak di atas trigger editor: " + json.dumps(z_state))
    if width <= 600:
        await assert_mobile_modal_image(modal, label)


async def assert_comparison_round1(page, width, label):
    sections = page.locator(".comp-category-section")
    if await sections.count() == 0:
        fail(label + ": comparison sections tidak tersedia")
    if await page.locator(".comp-table-hint").count():
        fail(label + ": hint swipe lama masih ada")

    selector = page.get_by_label("Bandingkan AQUA dengan", exact=True)
    if await selector.count() != 1:
        fail(label + ": selector mobile aksesibel wajib tepat satu")
    options = await selector.locator("option").all_inner_texts()
    values = await selector.locator("option").evaluate_all("nodes => nodes.map(node => node.value)")
    expected_options = ["LG", "MIDEA", "POLYTRON", "SAMSUNG", "SHARP"]
    if options != expected_options or values != expected_options:
        fail(label + ": opsi selector tidak exact/order: %s / %s" % (options, values))
    selector_display = await selector.locator("xpath=ancestor::div[contains(@class,'comp-mobile-brand-picker')]").evaluate(
        "node => getComputedStyle(node).display"
    )
    if width <= 600 and selector_display == "none":
        fail(label + ": selector mobile tidak terlihat")
    if width > 600 and selector_display != "none":
        fail(label + ": selector wajib mobile-only")

    async def comparison_state():
        return await sections.evaluate_all("""sections => {
            const visible = node => {
                const style = getComputedStyle(node);
                const rect = node.getBoundingClientRect();
                return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
            };
            return sections.map(section => ({
                headers: Array.from(section.querySelectorAll('thead th[data-brand]')).filter(visible).map(node => node.dataset.brand),
                rows: Array.from(section.querySelectorAll('tbody tr')).map(row =>
                    Array.from(row.querySelectorAll('td[data-brand]')).filter(visible).map(node => node.dataset.brand)),
                totalHeaders: section.querySelectorAll('thead th[data-brand]').length,
                totalCells: section.querySelectorAll('tbody td[data-brand]').length,
                totalActions: section.querySelectorAll('.comp-edit,.comp-del,.comp-add-cell').length,
                selectedMarks: Array.from(section.querySelectorAll('[data-selected-brand="true"]')).map(node => node.dataset.brand),
                wrapperOverflowX: getComputedStyle(section.querySelector('.comp-table-wrap')).overflowX
            }));
        }""")

    async def assert_brand_columns(expected, stage):
        state = await comparison_state()
        for index, section in enumerate(state):
            if section["headers"] != expected or any(row != expected for row in section["rows"]):
                fail(label + ": visible brand columns %s section %d bukan %s: %s" %
                     (stage, index, expected, json.dumps(section, ensure_ascii=False)))
            if section["totalHeaders"] != 6 or any(len(row) != 2 if width <= 600 else len(row) != 6 for row in section["rows"]):
                fail(label + ": jumlah kolom DOM/visible tidak sesuai kontrak: " + json.dumps(section, ensure_ascii=False))
        return state

    if width <= 600:
        first_mobile_check = await page.evaluate("!window.__mtmsMobileComparisonChecked")
        current_brand = await selector.input_value()
        if first_mobile_check and current_brand != "LG":
            fail(label + ": default selector mobile bukan LG")
        if current_brand != "LG":
            await selector.select_option("LG")
        before_switch = await assert_brand_columns(["AQUA", "LG"], "awal")
        await selector.select_option("SAMSUNG")
        after_switch = await assert_brand_columns(["AQUA", "SAMSUNG"], "switch Samsung")
        for before, after in zip(before_switch, after_switch):
            if ([before[key] for key in ("totalHeaders", "totalCells", "totalActions")] !=
                    [after[key] for key in ("totalHeaders", "totalCells", "totalActions")]):
                fail(label + ": switch Samsung menghilangkan data/action: %s -> %s" %
                     (json.dumps(before), json.dumps(after)))
            if not after["selectedMarks"] or any(brand != "SAMSUNG" for brand in after["selectedMarks"]):
                fail(label + ": penanda selected Samsung tidak konsisten: " + json.dumps(after))
        await page.evaluate("window.__mtmsMobileComparisonChecked = true")
    else:
        await assert_brand_columns(["AQUA", "LG", "MIDEA", "POLYTRON", "SAMSUNG", "SHARP"], "desktop")

    overflow = await page.evaluate("""() => ({
        page: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        wrappers: Array.from(document.querySelectorAll('.comp-table-wrap')).map(node => node.scrollWidth - node.clientWidth)
    })""")
    if overflow["page"] > 1 or (width <= 600 and any(value > 1 for value in overflow["wrappers"])):
        fail(label + ": horizontal overflow page/mobile wrapper: " + json.dumps(overflow))

    actions = page.locator(".comp-add-cell")
    if await actions.count() == 0:
        fail(label + ": fixture tidak punya sel kompetitor kosong")
    action_contract = await actions.evaluate_all("""nodes => nodes.map(node => ({
        actual: node.textContent.trim(),
        expected: 'Model ' + node.getAttribute('data-brand') + ' belum ada · Tambah'
    }))""")
    wrong_actions = [item for item in action_contract if item["actual"] != item["expected"]]
    if wrong_actions:
        fail(label + ": action sel kosong tidak spesifik merek: " + json.dumps(wrong_actions, ensure_ascii=False))

    await assert_min_font_size(page.locator(".comp-spec-item dt"), 12.8, label + " label tabel utama")
    await assert_min_font_size(page.locator(".comp-spec-item dd"), 13.0, label + " value tabel utama")
    await assert_min_font_size(page.locator(
        ".comp-add-cell, .comp-source, .comp-fitur-list li, .comp-detail-label, .comp-mobile-brand-picker"
    ), 12.5, label + " teks comparison")

    await page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
    await page.wait_for_timeout(THEME_SETTLE_MS)
    contrast = await actions.first.evaluate("""node => {
        const parse = value => (value.match(/[0-9.]+/g) || []).slice(0, 3).map(Number);
        const lum = value => {
            const rgb = parse(value).map(channel => {
                channel /= 255;
                return channel <= .03928 ? channel / 12.92 : Math.pow((channel + .055) / 1.055, 2.4);
            });
            return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
        };
        const style = getComputedStyle(node);
        const foreground = lum(style.color);
        const background = lum(style.backgroundColor);
        return (Math.max(foreground, background) + .05) / (Math.min(foreground, background) + .05);
    }""")
    await page.evaluate("document.documentElement.removeAttribute('data-theme')")
    if contrast < 4.5:
        fail(label + ": action sel kosong tidak terbaca di dark mode; contrast=%.2f" % contrast)


async def assert_compact_editor_trigger(page, width, label):
    trigger = page.locator(".ds-editor-fab")
    entry = page.locator(".ds-editor-entry")
    await trigger.wait_for(state="visible", timeout=5000)
    if not await trigger.is_enabled():
        fail(label + ": trigger editor belum aktif")
    if await page.get_by_role("button", name="Editor spesifikasi", exact=True).count() != 1:
        fail(label + ": accessible name Editor spesifikasi hilang")
    geometry = await page.evaluate("""() => {
        const hero = document.querySelector('.hero-mini');
        const entry = document.querySelector('.ds-editor-entry');
        const trigger = document.querySelector('.ds-editor-fab');
        const shell = document.querySelector('.ds-editor-shell');
        const rect = node => {
            const value = node.getBoundingClientRect();
            return {left: value.left, right: value.right, top: value.top, bottom: value.bottom,
                width: value.width, height: value.height};
        };
        const visible = node => {
            const style = getComputedStyle(node);
            const value = node.getBoundingClientRect();
            return style.display !== 'none' && style.visibility !== 'hidden' && value.width > 0 && value.height > 0;
        };
        const intersects = (left, right) => left.left < right.right - .5 && left.right > right.left + .5 &&
            left.top < right.bottom - .5 && left.bottom > right.top + .5;
        const entryRect = rect(entry);
        const triggerRect = rect(trigger);
        const content = Array.from(document.querySelectorAll(
            '.comp-full-table,.comp-model-info,.comp-spec-list,.pk-grid,.pk-card,.pk-spec-row,.pk-modal-right table'
        )).filter(node => visible(node) && !node.closest('.hero-mini') && !node.closest('.ds-editor-shell'));
        return {
            hero: rect(hero), entry: entryRect, trigger: triggerRect,
            entryParent: entry.parentElement === hero ? 'hero' : entry.parentElement === document.body ? 'body' : 'other',
            shellParent: shell.parentElement === document.body,
            entryPosition: getComputedStyle(entry).position,
            triggerPosition: getComputedStyle(trigger).position,
            visualLabel: trigger.textContent.trim(),
            intersects: content.filter(node => intersects(entryRect, rect(node)) || intersects(triggerRect, rect(node)))
                .map(node => node.className || node.tagName)
        };
    }""")
    hero = geometry["hero"]
    for key in ("entry", "trigger"):
        rect = geometry[key]
        contained = (rect["left"] >= hero["left"] - 1 and rect["right"] <= hero["right"] + 1 and
                     rect["top"] >= hero["top"] - 1 and rect["bottom"] <= hero["bottom"] + 1)
        if not contained:
            fail(label + ": rect %s tidak berada di hero: %s" % (key, json.dumps(geometry)))
    if geometry["entryParent"] != "hero" or not geometry["shellParent"]:
        fail(label + ": editor entry wajib child hero dan shell tetap body: " + json.dumps(geometry))
    if geometry["entryPosition"] in ("fixed", "absolute", "sticky") or geometry["triggerPosition"] in ("fixed", "absolute", "sticky"):
        fail(label + ": editor entry/trigger bukan normal flow: " + json.dumps(geometry))
    if geometry["trigger"]["width"] < 44 or geometry["trigger"]["height"] < 44 or geometry["visualLabel"] != "Editor spesifikasi":
        fail(label + ": trigger wajib >=44px dengan label visual penuh: " + json.dumps(geometry))
    if geometry["intersects"]:
        fail(label + ": editor intersect visible table/model/spec: " + json.dumps(geometry, ensure_ascii=False))
    if width <= 700:
        await trigger.click()
        shell = page.locator(".ds-editor-shell")
        await shell.wait_for(state="visible", timeout=2000)
        await shell.locator(".ds-editor-close").click()
        await shell.wait_for(state="hidden", timeout=2000)


async def assert_editor_sabotage(page, width, label):
    entry = page.locator(".ds-editor-entry")
    target = page.locator(".comp-full-table,.pk-grid,.pk-card").first
    await target.wait_for(state="visible", timeout=5000)
    original_style = await entry.get_attribute("style")
    target_rect = await target.evaluate("node => { const rect = node.getBoundingClientRect(); return {top: rect.top, left: rect.left}; }")
    await entry.evaluate("""(node, point) => {
        node.style.position = 'fixed';
        node.style.zIndex = '999';
        node.style.top = Math.max(0, point.top) + 'px';
        node.style.left = Math.max(0, point.left) + 'px';
        node.style.margin = '0';
    }""", target_rect)
    detected = False
    try:
        await assert_compact_editor_trigger(page, width, label + " sabotage intersect")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase final: verifier tidak merah saat editor dibuat overlay/intersect")
    await entry.evaluate("(node, style) => { if (style === null) node.removeAttribute('style'); else node.setAttribute('style', style); }", original_style)


async def assert_dark_readable(page, modal, label):
    await page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
    await page.wait_for_timeout(THEME_SETTLE_MS)
    colors = await modal.locator(".pk-spec-group").first.evaluate("""node => {
        const heading = node.querySelector("h5");
        const value = node.querySelector(".pk-spec-value");
        return {
            groupBackground: getComputedStyle(node).backgroundColor,
            headingColor: getComputedStyle(heading).color,
            headingBackground: getComputedStyle(heading).backgroundColor,
            valueColor: value ? getComputedStyle(value).color : ""
        };
    }""")
    if not colors["headingColor"] or not colors["valueColor"] or colors["headingColor"] == colors["headingBackground"]:
        fail(label + ": warna dark tidak terbaca: " + json.dumps(colors))
    await page.evaluate("document.documentElement.removeAttribute('data-theme')")


async def assert_main_table_contract(page, categories, record, brand):
    trigger = page.locator('.comp-detail-trigger[data-brand="%s"][data-model="%s"]' % (brand, record["model"]))
    cell = trigger.locator("xpath=ancestor::td[1]")
    expected_categories = active_categories(categories, comparison=True)
    actual_keys = await cell.locator(".comp-spec-item").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('data-spec-key'))"
    )
    expected_keys = [category["key"] for category in expected_categories]
    if actual_keys != expected_keys:
        fail("Tabel kompetitor: key comparison tidak exact/order: actual=%s expected=%s" % (actual_keys, expected_keys))
    for category in expected_categories:
        row = cell.locator('.comp-spec-item[data-spec-key="%s"]' % category["key"])
        actual = (await row.locator("dd").inner_text()).strip()
        expected = expected_spec_text(record.get("spec_values", {}).get(category["key"]), category)
        if actual != expected:
            fail("Tabel kompetitor %s: nilai %s bukan exact spec_values: %r != %r" % (record["model"], category["key"], actual, expected))
    if await page.locator('.comp-spec-list [data-spec-key="%s"]' % ADDITIONAL_KEY).count():
        fail("Tabel kompetitor: kategori additional/comparison=false bocor ke tabel utama")


async def assert_additional_present(modal, record):
    row = modal.locator('.pk-spec-row[data-spec-key="%s"]' % ADDITIONAL_KEY)
    if await row.count() != 1:
        fail("Modal: kategori additional terisi wajib tampil tepat sekali")
    expected = ", ".join(record["spec_values"][ADDITIONAL_KEY]["value"])
    if expected not in await row.inner_text():
        fail("Modal: nilai list additional tidak berasal dari spec_values exact")


async def assert_grouped_provenance(modal, label):
    groups = modal.locator(".pk-feature-provenance,.pk-spec-provenance,.pk-suggestion-provenance")
    if await groups.count() == 0:
        fail(label + ": grouped provenance tidak ditemukan")
    structure = await groups.evaluate_all("""groups => groups.map(group => {
        const direct = Array.from(group.children);
        const style = getComputedStyle(group);
        return {
            className: group.className,
            grouped: group.classList.contains('pk-provenance') && group.dataset.provenanceGroup === 'true',
            display: style.display,
            columns: style.gridTemplateColumns.split(/\\s+/).filter(Boolean).length,
            rowCount: group.querySelectorAll(':scope > .pk-provenance-row[data-provenance-field]').length,
            childCount: direct.length,
            fields: direct.map(row => row.getAttribute('data-provenance-field')),
            everyRow: direct.every(row => row.classList.contains('pk-provenance-row'))
        };
    })""")
    width = await modal.evaluate("root => window.innerWidth")
    for group in structure:
        if not group["grouped"] or group["display"] != "grid" or not group["everyRow"] or group["rowCount"] != group["childCount"]:
            fail(label + ": provenance masih inline padat/bukan row terpisah: " + json.dumps(group, ensure_ascii=False))
        if not group["fields"] or any(not field for field in group["fields"]):
            fail(label + ": provenance row kehilangan penanda field stabil: " + json.dumps(group, ensure_ascii=False))
        if width <= 600 and group["columns"] != 1:
            fail(label + ": grouped provenance mobile bukan satu kolom: " + json.dumps(group, ensure_ascii=False))
    await assert_min_font_size(groups.locator(".pk-provenance-row,.pk-provenance-row *"), 12.8, label + " grouped provenance")

    required = modal.locator('.pk-spec-row[data-spec-key="%s"] .pk-spec-provenance' % ADDITIONAL_KEY)
    required_fields = await required.locator(":scope > .pk-provenance-row").evaluate_all(
        "rows => rows.map(row => row.getAttribute('data-provenance-field'))"
    )
    expected_fields = ["source-link", "source-kind", "verified-at", "origin", "user-protection"]
    if required_fields != expected_fields:
        fail(label + ": row provenance spec tidak lengkap/order: %s != %s" % (required_fields, expected_fields))


async def assert_dynamic_modal(modal, categories, record, feature_sentinel, label):
    expected_categories = active_categories(categories)
    expected_keys = [category["key"] for category in expected_categories]
    populated = await modal.locator(".pk-spec-row").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('data-spec-key'))"
    )
    missing_attrs = await modal.locator(".pk-spec-missing").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('data-missing-keys') || '')"
    )
    missing = [key for attr in missing_attrs for key in attr.split(",") if key]
    rendered_keys = populated + missing
    if len(rendered_keys) != len(set(rendered_keys)) or set(rendered_keys) != set(expected_keys):
        fail(label + ": modal tidak mencakup exact semua kategori aktif: rendered=%s expected=%s" % (rendered_keys, expected_keys))

    expected_groups = []
    for category in expected_categories:
        if category["group"] not in expected_groups:
            expected_groups.append(category["group"])
    actual_groups = await modal.locator(".pk-spec-group").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('data-spec-group'))"
    )
    if actual_groups != expected_groups:
        fail(label + ": group/order modal tidak exact: actual=%s expected=%s" % (actual_groups, expected_groups))

    await assert_additional_present(modal, record)
    live_row = modal.locator('.pk-spec-row[data-spec-key="%s"]' % LIVE_CATEGORY_KEY)
    if await live_row.count() != 1 or LIVE_CATEGORY_VALUE not in await live_row.inner_text():
        fail(label + ": kategori/data live tidak tampil setelah refresh")
    wifi = modal.locator('.pk-spec-row[data-spec-key="wifi"] .pk-spec-value')
    if await wifi.count() != 1 or (await wifi.inner_text()).strip() != "Ya":
        fail(label + ": boolean true wajib berformat Ya")
    defrost = modal.locator('.pk-spec-row[data-spec-key="defrost_type"] .pk-spec-value')
    if await defrost.count() != 1 or (await defrost.inner_text()).strip() != "Tidak":
        fail(label + ": boolean false wajib berformat Tidak")
    rated = (await modal.locator('.pk-spec-row[data-spec-key="rated_power_w"] .pk-spec-value').inner_text()).strip()
    if rated != "88 W" or rated.lower().count("w") != 1:
        fail(label + ": unit W terduplikasi atau berubah: " + rated)
    door = (await modal.locator('.pk-spec-row[data-spec-key="door_count"] .pk-spec-value').inner_text()).strip()
    if door != "3 pintu" or door.lower().count("pintu") != 1:
        fail(label + ": unit pintu terduplikasi atau berubah: " + door)

    missing_keys = set(missing)
    if not {"net_capacity_l", "depth_mm"}.issubset(missing_keys):
        fail(label + ": missing sparse tidak diringkas jujur per group: " + repr(missing_keys))
    if await modal.locator('.pk-spec-row[data-spec-key="net_capacity_l"], .pk-spec-row[data-spec-key="depth_mm"]').count():
        fail(label + ": missing sparse masih dirender sebagai row besar")

    provenance = modal.locator('.pk-spec-row[data-spec-key="%s"] .pk-spec-provenance' % ADDITIONAL_KEY)
    provenance_text = " ".join((await provenance.inner_text()).split())
    for sentinel in ("Jenis sumber: Halaman produk resmi", "Diverifikasi:", "WIB", "Asal data: Hasil riset", "Perlindungan nilai: dapat diperbarui dari riset"):
        if sentinel not in provenance_text:
            fail(label + ": provenance nilai kurang " + sentinel)
    if FIXTURE_SOURCE_KIND in provenance_text or FIXTURE_VERIFIED_AT in provenance_text or "Kunci user" in await modal.inner_text():
        fail(label + ": provenance mentah/wording teknis masih tampil ke user")
    source_kind = provenance.locator('[data-source-kind="%s"]' % FIXTURE_SOURCE_KIND)
    if await source_kind.count() != 1:
        fail(label + ": raw source_kind tidak dipertahankan pada atribut data")
    verified_time = provenance.locator('time[datetime="%s"]' % FIXTURE_VERIFIED_AT)
    if await verified_time.count() != 1 or "WIB" not in await verified_time.inner_text():
        fail(label + ": verified_at tidak human-readable WIB dengan raw datetime utuh")
    origin_expectations = {
        ADDITIONAL_KEY: ("research", "Asal data: Hasil riset"),
        "door_count": ("user", "Asal data: Masukan pengguna"),
        "gross_capacity_l": ("legacy", "Asal data: Data lama"),
        "height_mm": ("unknown", "Asal data: Belum diketahui"),
    }
    for key, (raw_origin, visible_label) in origin_expectations.items():
        origin = modal.locator('.pk-spec-row[data-spec-key="%s"] [data-origin="%s"]' % (key, raw_origin))
        if await origin.count() != 1 or visible_label not in " ".join((await origin.inner_text()).split()):
            fail(label + ": origin %s tidak dipetakan ke label Indonesia" % raw_origin)
    protected = modal.locator('.pk-spec-row[data-spec-key="door_count"] [data-user-protection="protected"]')
    if await protected.count() != 1 or "tidak dapat ditimpa otomatis" not in " ".join((await protected.inner_text()).split()):
        fail(label + ": perlindungan nilai user-locked tidak dijelaskan dengan bahasa awam")
    expected_source = record["spec_values"][ADDITIONAL_KEY]["source_url"]
    if await provenance.locator('a[href="%s"]' % expected_source).count() != 1:
        fail(label + ": safe https source link nilai tidak tampil")
    same_origin_source = modal.locator('.pk-spec-row[data-spec-key="compressor_type"] .pk-spec-provenance')
    if await same_origin_source.locator('a[href="%s"]' % SAFE_SAME_ORIGIN_SOURCE).count() != 1:
        fail(label + ": safe same-origin relative source link tidak tampil")
    if await modal.locator(
            '.pk-spec-row[data-spec-key="wifi"] .pk-spec-provenance a, '
            '.pk-spec-row[data-spec-key="defrost_type"] .pk-spec-provenance a').count():
        fail(label + ": protocol-relative/javascript spec source menjadi link")

    statuses = await modal.locator(".pk-suggestion").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('data-suggestion-status'))"
    )
    if statuses != ["pending", "accepted", "rejected", "rejected", "rejected", "rejected"]:
        fail(label + ": status suggestion tidak lengkap/order: " + repr(statuses))
    if await modal.locator(".pk-suggestion.is-pending").count() != 1:
        fail(label + ": pending suggestion tidak punya penanda visual khusus")
    suggestion_styles = await modal.evaluate("""root => {
        const pending = root.querySelector(".pk-suggestion.is-pending");
        const accepted = root.querySelector(".pk-suggestion.is-accepted");
        return {
            pendingBackground: getComputedStyle(pending).backgroundColor,
            pendingBorder: getComputedStyle(pending).borderLeftColor,
            acceptedBackground: getComputedStyle(accepted).backgroundColor,
            acceptedBorder: getComputedStyle(accepted).borderLeftColor
        };
    }""")
    if (suggestion_styles["pendingBackground"] == suggestion_styles["acceptedBackground"] and
            suggestion_styles["pendingBorder"] == suggestion_styles["acceptedBorder"]):
        fail(label + ": pending suggestion tidak berbeda visual dari accepted: " + repr(suggestion_styles))
    suggestion_text = await modal.locator(".pk-research-suggestions").inner_text()
    for sentinel in ("Pending", "Diterima", "Ditolak", "Tipe Kulkas", "Usulan:", "Halaman produk resmi", "WIB"):
        if sentinel not in suggestion_text:
            fail(label + ": tampilan suggestion kurang " + sentinel)
    accepted_suggestion = modal.locator(".pk-suggestion.is-accepted")
    if await accepted_suggestion.locator('a[href="%s"]' % SAFE_SAME_ORIGIN_SUGGESTION).count() != 1:
        fail(label + ": safe same-origin relative suggestion link tidak tampil")
    if await modal.locator(".pk-suggestion.is-rejected a").count():
        fail(label + ": protocol-relative/javascript/control/backslash suggestion URL menjadi link")
    raw_hrefs = await modal.locator("a").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('href') || '')"
    )
    unsafe_hrefs = [href for href in raw_hrefs if (
        href.startswith("//") or href.lower().startswith("javascript:") or "\\" in href or
        any(ord(character) < 32 or ord(character) == 127 for character in href)
    )]
    if unsafe_hrefs:
        fail(label + ": unsafe href lolos ke DOM: " + repr(unsafe_hrefs))
    if await modal.locator(".pk-fitur li", has_text=feature_sentinel).count() != 1:
        fail(label + ": feature bullet hilang: " + feature_sentinel)
    feature_meta = " ".join((await modal.locator(".pk-feature-provenance").inner_text()).split())
    if "Halaman produk resmi" not in feature_meta or "WIB" not in feature_meta or "Asal data: Hasil riset" not in feature_meta:
        fail(label + ": fitur_meta tidak dipertahankan")
    await assert_grouped_provenance(modal, label)


async def assert_sabotage_guard(page, modal, categories, record, width, label):
    await assert_additional_present(modal, record)
    removed = await modal.locator('.pk-spec-row[data-spec-key="%s"]' % ADDITIONAL_KEY).evaluate(
        "node => { node.remove(); return true; }"
    )
    if not removed:
        fail("Sabotase: row additional tidak berhasil disuppress")
    detected = False
    try:
        await assert_additional_present(modal, record)
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase: verifier tidak merah saat modal additional disuppress")
    await page.evaluate("""payload => window.MTMSProductDetail.open(payload.record, {
        categories: payload.categories
    })""", {"record": record, "categories": categories["spec_categories"]})
    restored = await wait_modal(page)
    await assert_additional_present(restored, record)

    active_button = restored.get_by_role("button", name="Ringkasan", exact=True)
    await active_button.evaluate("node => node.removeAttribute('aria-current')")
    detected = False
    try:
        await assert_modal_round1(page, restored, record, width, label + " sabotage active nav")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase final: verifier tidak merah saat active nav aksesibel dihapus")

    await page.evaluate("""payload => window.MTMSProductDetail.open(payload.record, {
        categories: payload.categories
    })""", {"record": record, "categories": categories["spec_categories"]})
    restored = await wait_modal(page)

    await restored.get_by_role("button", name="Spesifikasi", exact=True).evaluate("node => node.remove()")
    detected = False
    try:
        await assert_modal_round1(page, restored, record, width, label + " sabotage nav")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase round-1: verifier tidak merah saat tombol nav Spesifikasi dihapus")

    await page.evaluate("""payload => window.MTMSProductDetail.open(payload.record, {
        categories: payload.categories
    })""", {"record": record, "categories": categories["spec_categories"]})
    restored = await wait_modal(page)
    provenance = restored.locator(".pk-spec-provenance").first
    original_style = await provenance.get_attribute("style")
    await provenance.evaluate("node => { node.style.fontSize = '10px'; }")
    detected = False
    try:
        await assert_min_font_size(provenance, 12.8, label + " sabotage fontSize")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase round-1: verifier tidak merah saat font provenance menjadi 10px")
    await provenance.evaluate("(node, style) => { if (style === null) node.removeAttribute('style'); else node.setAttribute('style', style); }", original_style)

    provenance_row = provenance.locator(":scope > .pk-provenance-row").first
    await provenance_row.evaluate("node => node.classList.remove('pk-provenance-row')")
    detected = False
    try:
        await assert_grouped_provenance(restored, label + " sabotage grouped provenance")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase final: verifier tidak merah saat provenance row diratakan")

    await page.evaluate("""payload => window.MTMSProductDetail.open(payload.record, {
        categories: payload.categories
    })""", {"record": record, "categories": categories["spec_categories"]})
    restored = await wait_modal(page)

    bottom_marker = restored.locator('[data-detail-bottom="true"]')
    original_style = await bottom_marker.get_attribute("style")
    await bottom_marker.evaluate("node => { node.style.display = 'none'; }")
    detected = False
    try:
        await assert_modal_scroll_path(restored, label + " sabotage bottom")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase final: verifier tidak merah saat bottom cue disembunyikan")
    await bottom_marker.evaluate("(node, style) => { if (style === null) node.removeAttribute('style'); else node.setAttribute('style', style); }", original_style)

    if width <= 600:
        image = restored.locator(".pk-gal-img").first
        original_style = await image.get_attribute("style")
        await image.evaluate("node => { node.style.height = '220px'; node.style.maxHeight = '220px'; }")
        detected = False
        try:
            await assert_mobile_modal_image(restored, label + " sabotage image")
        except AssertionError:
            detected = True
        if not detected:
            fail("Sabotase round-1: verifier tidak merah saat gambar mobile menjadi 220px")
        await image.evaluate("(node, style) => { if (style === null) node.removeAttribute('style'); else node.setAttribute('style', style); }", original_style)

    without_suggestions = copy.deepcopy(record)
    without_suggestions["research_suggestions"] = []
    await page.evaluate("""payload => window.MTMSProductDetail.open(payload.record, {
        categories: payload.categories
    })""", {"record": without_suggestions, "categories": categories["spec_categories"]})
    without_modal = await wait_modal(page)
    without_labels = await without_modal.locator(".pk-detail-nav button").all_inner_texts()
    if without_labels != ["Ringkasan", "Fitur", "Spesifikasi"] or await without_modal.locator("#mtms-product-detail-saran").count():
        fail(label + ": nav Saran riset wajib diomit ketika suggestion kosong")

    await page.evaluate("""payload => window.MTMSProductDetail.open(payload.record, {
        categories: payload.categories
    })""", {"record": record, "categories": categories["spec_categories"]})
    await wait_modal(page)


async def assert_comparison_sabotage(page, width, label):
    action = page.locator(".comp-add-cell").first
    original_text = await action.inner_text()
    await action.evaluate("node => { node.textContent = '+ Tambah Model'; }")
    detected = False
    try:
        await assert_comparison_round1(page, width, label + " sabotage brand action")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase round-1: verifier tidak merah saat action sel kosong menjadi generik")
    await action.evaluate("(node, text) => { node.textContent = text; }", original_text)

    selected_cell = page.locator('.comp-category-section').first.locator('tbody tr').first.locator('td[data-brand="LG"]')
    original_style = await selected_cell.get_attribute("style")
    await selected_cell.evaluate("node => { node.style.display = 'none'; }")
    detected = False
    try:
        await assert_comparison_round1(page, width, label + " sabotage visible brand")
    except AssertionError:
        detected = True
    if not detected:
        fail("Sabotase final: verifier tidak merah saat satu brand column disembunyikan")
    await selected_cell.evaluate("(node, style) => { if (style === null) node.removeAttribute('style'); else node.setAttribute('style', style); }", original_style)

    if width <= 600:
        picker = page.locator(".comp-mobile-brand-picker")
        original_style = await picker.get_attribute("style")
        await picker.evaluate("node => { node.style.display = 'none'; }")
        detected = False
        try:
            await assert_comparison_round1(page, width, label + " sabotage selector")
        except AssertionError:
            detected = True
        if not detected:
            fail("Sabotase final: verifier tidak merah saat selector mobile disembunyikan")
        await picker.evaluate("(node, style) => { if (style === null) node.removeAttribute('style'); else node.setAttribute('style', style); }", original_style)


async def wait_research_log(predicate, timeout_ms=5000):
    deadline = asyncio.get_running_loop().time() + timeout_ms / 1000
    while asyncio.get_running_loop().time() < deadline:
        for entry in Handler.research["log"]:
            if predicate(entry):
                return entry
        await page_sleep(100)
    fail("log riset tidak memuat entri yang diharapkan dalam batas waktu")


async def assert_row_edit_focus(page, width, label):
    row = page.locator(
        '.comp-category-section').first.locator(
        'tbody tr').first.locator('td.comp-aqua .comp-spec-item.comp-spec-editable[data-spec-key="form_factor"]')
    if await row.count() != 1:
        fail(label + ": baris spesifikasi editable tidak exact satu: " + str(await row.count()))
    model_id = await row.get_attribute("data-edit-model")
    if not model_id or not model_id.startswith("AQUA::"):
        fail(label + ": data-edit-model hilang/salah: " + repr(model_id))
    await row.scroll_into_view_if_needed()
    await row.click()
    pop = page.locator(".comp-mini-edit")
    try:
        await pop.wait_for(state="visible", timeout=4000)
    except AssertionError:
        fail(label + ": klik baris tidak memunculkan popup ubah-satu-kolom")
    mini_input = pop.locator(".comp-mini-input")
    if await mini_input.count() != 1:
        fail(label + ": input popup mini hilang")
    focused_class = await page.evaluate("document.activeElement && document.activeElement.className") or ""
    if "comp-mini-input" not in focused_class:
        fail(label + ": fokus tidak mendarat di input popup mini: " + repr(focused_class))
    await mini_input.fill("999")
    log_len_before = len(Handler.research["log"])
    patch_before = len([e for e in Handler.research["log"]
                        if e.get("method") == "PATCH" and e.get("path") == "/api/kompetitor"])
    await pop.locator(".comp-mini-save").click()
    saved_entry = await wait_research_log(lambda entry: entry.get("method") == "PATCH" and
                                          entry.get("path") == "/api/kompetitor" and
                                          isinstance(entry.get("body"), dict) and
                                          entry["body"].get("key") == "form_factor",
                                          timeout_ms=5000)
    fresh_entries = Handler.research["log"][log_len_before:]
    if len([e for e in fresh_entries if e.get("method") == "PATCH" and
            e.get("path") == "/api/kompetitor"]) != 1:
        recent = [e for e in Handler.research["log"]
                  if e.get("method") == "PATCH" and e.get("path") == "/api/kompetitor"][-6:]
        fail(label + ": simpan mini mengirim PATCH tidak tepat satu; terakhir: " +
             json.dumps(recent, ensure_ascii=False)[:1200])
    if saved_entry["if_match"] != '"' + FIXTURE_SHA + '"':
        fail(label + ": simpan mini wajib bawa If-Match SHA terkini: " + repr(saved_entry["if_match"]))
    body = saved_entry["body"]
    if body.get("action") != "set_spec_value" or body.get("model_id") != model_id or \
            body.get("entry", {}).get("value") != "999":
        fail(label + ": payload simpan mini salah: " + json.dumps(body, ensure_ascii=False))
    try:
        await page.wait_for_function(
            """selector => {
                const row = document.querySelector(selector);
                const dd = row && row.querySelector('dd');
                return !!dd && dd.textContent.indexOf('999') !== -1;
            }""", arg='.comp-category-section tbody tr td.comp-aqua .comp-spec-item[data-spec-key="form_factor"]',
            timeout=4000)
    except Exception:
        fail(label + ": nilai kolom tidak terbarui jadi 999 setelah simpan")

    # Escape menutup popup tanpa menyimpan
    await row.click()
    try:
        await pop.wait_for(state="visible", timeout=3000)
    except AssertionError:
        fail(label + ": klik baris kedua tidak memunculkan popup lagi")
    await page.keyboard.press("Escape")
    try:
        await pop.wait_for(state="hidden", timeout=2500)
    except Exception:
        fail(label + ": Escape tidak menutup popup mini")

    # Sabotase: class editable dihapus -> klik tidak boleh memunculkan popup
    await row.evaluate("node => node.classList.remove('comp-spec-editable')")
    bare_row = page.locator('.comp-category-section').first.locator('tbody tr').first.locator(
        'td.comp-aqua .comp-spec-item[data-spec-key="form_factor"]')
    if await bare_row.count() != 1:
        fail(label + ": baris sabotase hilang dari DOM")
    await bare_row.click()
    await page.wait_for_timeout(900)
    if await page.locator(".comp-mini-edit").count():
        fail(label + ": sabotase baris non-editable masih memunculkan popup")


async def page_sleep(ms):
    await asyncio.sleep(ms / 1000)


async def assert_inline_editor(page, width, label):
    buttons = page.locator(".comp-edit:enabled")
    if await buttons.count() == 0:
        fail(label + ": tidak ada tombol Edit kolom aktif")
    first = buttons.first
    brand = await first.get_attribute("data-brand")
    model = await first.get_attribute("data-model")
    if not brand or not model:
        fail(label + ": tombol Edit kolom kehilangan data-brand/model")
    await first.click()
    shell = page.locator(".ds-editor-shell")
    try:
        await shell.wait_for(state="visible", timeout=4000)
    except AssertionError:
        fail(label + ": Edit kolom tidak membuka editor spesifikasi langsung")
    select = shell.locator("[data-ds-model-select]")
    if await select.count() != 1:
        fail(label + ": pilih model di editor hilang")
    value = await select.input_value()
    if value != brand + "::" + model:
        fail(label + ": editor tidak membuka model kolom yang ditekan: %s != %s" %
             (value, brand + "::" + model))
    await page.keyboard.press("Escape")
    await shell.wait_for(state="hidden", timeout=4000)


async def assert_research_ui(page, modal, competitor_brand, competitor_model, comp_trigger, label):
    model_id = competitor_brand + "::" + competitor_model

    async def research_box_present(opened):
        box = opened.locator('.pk-research[data-model-id="%s"]' % model_id)
        if await box.count() != 1:
            fail(label + ": riset box tidak exact satu untuk " + model_id)
        return box

    def entries(method=None, action=None):
        result = []
        for entry in Handler.research["log"]:
            if method and entry.get("method") != method:
                continue
            body = entry.get("body")
            if action and (not isinstance(body, dict) or body.get("action") != action):
                continue
            result.append(entry)
        return result

    box = await research_box_present(modal)
    start = box.locator(".pk-research-start")
    if not await start.is_enabled():
        fail(label + ": tombol riset harus aktif saat data live siap")

    post_before = len(entries("POST"))
    await start.click()
    candidate = modal.locator(".pk-research-candidate.is-pending")
    await candidate.wait_for(state="visible", timeout=6000)
    posts = entries("POST")
    if len(posts) != post_before + 1:
        fail(label + ": klik Riset ulang wajib tepat satu POST")
    if posts[-1]["body"] != {"model_id": model_id}:
        fail(label + ": POST body bukan exact {model_id}: " + json.dumps(posts[-1], ensure_ascii=False))
    card_text = " ".join((await candidate.inner_text()).split())
    if "Jenis Kompresor" not in card_text or RESEARCH_CANDIDATE_VALUE not in card_text:
        fail(label + ": kandidat tidak menampilkan label kategori/nilai: " + card_text[:200])
    if "Halaman produk resmi" not in card_text or "WIB" not in card_text:
        fail(label + ": kandidat kehilangan provenance WIB/jenis sumber")

    accept_patch_before = len(entries("PATCH", "accept"))
    kompetitor_get_marker = len(entries("GET"))
    await candidate.locator(".pk-research-accept").click()
    accept_entry = await wait_research_log(
        lambda entry: entry.get("method") == "PATCH" and isinstance(entry.get("body"), dict) and
        entry["body"].get("action") == "accept" and
        isinstance(entry["body"].get("suggestion_id"), str),
        timeout_ms=6000)
    if accept_entry["if_match"] != '"' + FIXTURE_SHA + '"':
        fail(label + ": accept wajib membawa If-Match SHA data terkini: " + repr(accept_entry["if_match"]))
    if len(entries("PATCH", "accept")) != accept_patch_before + 1:
        fail(label + ": accept mengirim lebih dari satu PATCH")
    deadline = asyncio.get_running_loop().time() + 6
    refreshed = False
    while asyncio.get_running_loop().time() < deadline:
        gets = [entry for entry in Handler.research["log"][Handler.research["log"].index(accept_entry) + 1:]
                if entry.get("method") == "GET" and entry.get("path") == "/api/kompetitor"]
        if gets:
            refreshed = True
            break
        await page_sleep(100)
    if not refreshed:
        fail(label + ": accept sukses tidak memicu refresh data (onChanged)")
    await modal.locator(".pk-modal-close").click()
    await modal.wait_for(state="hidden")

    await comp_trigger.click()
    reopened = await wait_modal(page)
    box = await research_box_present(reopened)
    await box.locator(".pk-research-start").click()
    pending = reopened.locator(".pk-research-candidate.is-pending")
    await pending.wait_for(state="visible", timeout=6000)
    reject_patch_before = len(entries("PATCH", "reject"))
    await pending.locator(".pk-research-reject").click()
    await wait_research_log(
        lambda entry: entry.get("method") == "PATCH" and isinstance(entry.get("body"), dict) and
        entry["body"].get("action") == "reject",
        timeout_ms=6000)
    if len(entries("PATCH", "reject")) != reject_patch_before + 1:
        fail(label + ": reject mengirim lebih dari satu PATCH")
    rejected_card = reopened.locator(".pk-research-candidate.is-rejected")
    try:
        await rejected_card.first.wait_for(state="visible", timeout=5000)
    except Exception:
        fail(label + ": kartu usulan tidak berubah jadi ditolak")
    status_text = await reopened.locator(".pk-research-status").inner_text()
    if "ditolak" not in status_text.lower():
        fail(label + ": status tolak tidak tampil: " + status_text)

    await reopened.locator(".pk-modal-close").click()
    await reopened.wait_for(state="hidden")
    log_len = len(Handler.research["log"])
    await page_sleep(700)
    if len(Handler.research["log"]) != log_len:
        fail(label + ": polling masih jalan setelah modal ditutup: " +
             json.dumps(Handler.research["log"][log_len:], ensure_ascii=False))

    await comp_trigger.click()
    sabotaged = await wait_modal(page)
    await sabotaged.locator(".pk-research").first.evaluate("node => node.remove()")
    detected = False
    try:
        await research_box_present(sabotaged)
    except AssertionError:
        detected = True
    if not detected:
        fail(label + ": sabotase riset box dihapus tidak membuat verifier merah")


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
    await page.route("**/api/spec-categories", delayed_api)
    started = asyncio.get_running_loop().time()
    await page.goto(base + "/kompetitor.html", wait_until="domcontentloaded")
    await page.locator(".comp-detail-trigger").first.wait_for(state="visible", timeout=5000)
    elapsed = asyncio.get_running_loop().time() - started
    if elapsed >= 1.2:
        fail("Kompetitor: render data bawaan terlalu lambat %.3fs; errors=%s" % (elapsed, json.dumps(errors)))
    if await page.evaluate("window.MTMS_COMPETITOR_LIVE_READY !== false"):
        fail("Kompetitor: fixture API tertunda tidak membuktikan render sebelum API")
    await page.locator(".comp-detail-trigger").first.click()
    early_modal = await wait_modal(page)
    early_start = early_modal.locator(".pk-research-start")
    if await early_start.count() != 1:
        fail("Kompetitor: tombol Riset ulang wajib ada di modal sejak awal")
    if await early_start.is_enabled():
        fail("Kompetitor: Riset ulang aktif sebelum data live; harus disabled")
    early_hint = (await early_modal.locator(".pk-research-status").inner_text()).strip()
    if "data live" not in early_hint:
        fail("Kompetitor: hint menunggu data live tidak tampil: " + early_hint)
    await page.keyboard.press("Escape")
    await early_modal.wait_for(state="hidden")
    first_keys = await page.locator(".comp-spec-list").first.locator(".comp-spec-item").evaluate_all(
        "nodes => nodes.map(node => node.getAttribute('data-spec-key'))"
    )
    with open(CATEGORIES_PATH, encoding="utf-8") as fh:
        static_categories = json.load(fh)
    expected_first = [item["key"] for item in static_categories["spec_categories"]
                      if item["active"] is True and item["comparison"] is True]
    if len(expected_first) < 8:
        fail("Kompetitor: registry kategori comparison terlalu sedikit: " + repr(expected_first))
    if first_keys != expected_first:
        fail("Kompetitor: fallback tabel tidak exact ikut registry comparison: " +
             repr(first_keys) + " != " + repr(expected_first))
    await page.wait_for_function("window.MTMS_COMPETITOR_LIVE_READY === true", timeout=10000)
    await page.wait_for_function("window.MTMSSpecCategories.getState().source === 'api'", timeout=10000)
    if await page.locator(".comp-edit:enabled").count() == 0:
        fail("Kompetitor: tombol edit tidak aktif sesudah data live selesai")
    await page.close()

    page = await browser.new_page(viewport={"width": 1440, "height": 900})
    await page.route("**/api/produk", delayed_api)
    await page.route("**/api/foto", delayed_api)
    await page.route("**/api/spec-categories", delayed_api)
    started = asyncio.get_running_loop().time()
    await page.goto(base + "/produk.html", wait_until="domcontentloaded")
    await page.locator(".pk-card").first.wait_for(state="visible", timeout=5000)
    elapsed = asyncio.get_running_loop().time() - started
    if elapsed >= 1.2:
        fail("Produk: render data bawaan terlalu lambat %.3fs" % elapsed)
    if await page.locator(".pk-edit-add").count():
        fail("Produk: editor aktif sebelum data live selesai")
    await page.wait_for_function("window.MTMS_DATA_LIVE === true", timeout=12000)
    await page.wait_for_function("window.MTMSSpecCategories.getState().source === 'api'", timeout=12000)
    await page.locator(".pk-edit-add").wait_for(state="visible", timeout=2000)
    await page.close()

    page = await browser.new_page(viewport={"width": 1440, "height": 900})
    await page.route("**/data/spec-categories.json", lambda route: route.abort())
    await page.route("**/api/spec-categories", lambda route: route.abort())
    started = asyncio.get_running_loop().time()
    await page.goto(base + "/kompetitor.html", wait_until="domcontentloaded")
    await page.locator(".comp-detail-trigger").first.wait_for(state="visible", timeout=5000)
    elapsed = asyncio.get_running_loop().time() - started
    if elapsed >= 1.2:
        fail("Kompetitor: fallback 12-core saat sumber kategori gagal terlalu lambat %.3fs" % elapsed)
    fallback_state = await page.evaluate("window.MTMSSpecCategories.getState()")
    if fallback_state["source"] != "fallback" or len(fallback_state["categories"]) != 12:
        fail("Kompetitor: kegagalan kategori tidak mempertahankan safe 12-core fallback: " + repr(fallback_state))
    await page.close()


async def assert_requested_product_refresh(browser, base, aqua_model):
    async def delayed_categories(route):
        await asyncio.sleep(0.7)
        await route.continue_()

    async def delayed_products(route):
        await asyncio.sleep(1.4)
        await route.continue_()

    page = await browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("console", lambda msg: errors.append("console-" + msg.type + ": " + msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append("pageerror: " + str(err)))
    await page.route("**/api/spec-categories", delayed_categories)
    await page.route("**/api/produk", delayed_products)
    await page.goto(base + "/produk.html?model=" + aqua_model, wait_until="domcontentloaded")
    modal = await wait_modal(page)
    initial_text = await modal.inner_text()
    if LIVE_CATEGORY_LABEL in initial_text or "CANONICAL_SENTINEL_FROM_PRODUCT_API" in initial_text:
        fail("Produk refresh: modal awal tidak membuktikan embedded-first sebelum kategori/data API")
    await page.wait_for_function("window.MTMSSpecCategories.getState().source === 'api'", timeout=5000)
    await page.wait_for_function("""value => {
        const current = document.querySelector('.pk-modal.open[data-mtms-product-detail="true"]');
        return !!current && current.textContent.includes(value) &&
            current.textContent.includes("CANONICAL_SENTINEL_FROM_PRODUCT_API");
    }""", arg=LIVE_CATEGORY_VALUE, timeout=7000)
    if not await modal.is_visible():
        fail("Produk refresh: modal requested tertutup ketika kategori/data live masuk")
    await assert_clean(page, errors, "produk requested refresh")
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


async def run_browser(base, fixture):
    aqua = fixture["aqua"]
    canonical_row = fixture["canonical_row"]
    categories = fixture["categories"]
    competitor = fixture["competitor"]
    competitor_fixture = fixture["competitor_fixture"]
    competitor_brand = fixture["competitor_brand"]
    async with async_playwright() as pw:
        launch = {"headless": True}
        if os.path.exists(CHROME):
            launch["executable_path"] = CHROME
        browser = await pw.chromium.launch(**launch)
        await assert_embedded_first_render(browser, base)
        await assert_requested_product_refresh(browser, base, aqua["model"])
        for width, height in ((1440, 900), (390, 844)):
            page = await browser.new_page(viewport={"width": width, "height": height})
            await install_listener_probe(page)
            errors = []
            page.on("console", lambda msg, bag=errors: bag.append("console-" + msg.type + ": " + msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err, bag=errors: bag.append("pageerror: " + str(err)))

            await page.goto(base + "/produk.html?model=" + aqua["model"], wait_until="networkidle")
            if not await page.evaluate("!!(window.MTMSProductDetail && typeof window.MTMSProductDetail.open === 'function')"):
                fail("Produk: singleton window.MTMSProductDetail.open belum tersedia")
            modal = await wait_modal(page)
            if "CANONICAL_SENTINEL_FROM_PRODUCT_API" not in await modal.inner_text():
                fail("Produk card: shared modal tidak memakai record API canonical")
            await assert_dynamic_modal(
                modal,
                categories,
                canonical_row,
                canonical_row["fitur"][0],
                "produk %dpx" % width,
            )
            await assert_modal_scroll_path(modal, "produk %dpx" % width)
            await assert_modal_round1(page, modal, canonical_row, width, "produk %dpx" % width)
            await assert_dark_readable(page, modal, "produk %dpx" % width)
            await assert_tap_targets(page, "produk modal %dpx" % width)
            await assert_sabotage_guard(page, modal, categories, canonical_row, width, "produk %dpx" % width)
            await page.keyboard.press("Escape")
            await modal.wait_for(state="hidden")
            restored = await page.evaluate("document.body.style.overflow")
            if restored:
                fail("Produk modal: body scroll tidak dipulihkan sesudah Escape")
            await assert_compact_editor_trigger(page, width, "produk %dpx" % width)
            await assert_editor_sabotage(page, width, "produk %dpx" % width)
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
            await install_listener_probe(page)
            errors = []
            page.on("console", lambda msg, bag=errors: bag.append("console-" + msg.type + ": " + msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err, bag=errors: bag.append("pageerror: " + str(err)))
            await page.goto(base + "/kompetitor.html", wait_until="networkidle")
            await page.wait_for_function("window.MTMSSpecCategories.getState().source === 'api'", timeout=5000)
            aqua_trigger = page.locator('.comp-detail-trigger[data-brand="AQUA"][data-model="%s"]' % aqua["model"])
            await aqua_trigger.wait_for(state="visible", timeout=5000)
            await assert_comparison_round1(page, width, "kompetitor %dpx" % width)
            await assert_comparison_sabotage(page, width, "kompetitor %dpx" % width)
            await assert_compact_editor_trigger(page, width, "kompetitor %dpx" % width)
            await assert_editor_sabotage(page, width, "kompetitor %dpx" % width)
            if width <= 600:
                await page.get_by_label("Bandingkan AQUA dengan", exact=True).select_option(competitor_brand)
            await assert_main_table_contract(page, categories, competitor_fixture, competitor_brand)
            await assert_inline_editor(page, width, "kompetitor %dpx" % width)
            await assert_row_edit_focus(page, width, "kompetitor %dpx" % width)
            await assert_tap_targets(page, "kompetitor tabel %dpx" % width)

            edit = page.locator('.comp-edit[data-brand="AQUA"][data-model="%s"]' % aqua["model"])
            await edit.click()
            if await page.locator('.pk-modal.open[data-mtms-product-detail="true"]').count():
                fail("Kompetitor Edit: klik Edit ikut membuka shared detail")
            editor_shell = page.locator(".ds-editor-shell")
            await editor_shell.wait_for(state="visible", timeout=4000)
            edit_select = editor_shell.locator("[data-ds-model-select]")
            if await edit_select.count() != 1 or (await edit_select.input_value()) != "AQUA::" + aqua["model"]:
                fail("Kompetitor Edit: tombol kolom tidak langsung membuka model AQUA di editor")
            await page.keyboard.press("Escape")
            await editor_shell.wait_for(state="hidden", timeout=4000)

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
            await assert_dynamic_modal(
                modal,
                categories,
                canonical_row,
                canonical_row["fitur"][0],
                "kompetitor AQUA %dpx" % width,
            )
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
            await assert_dynamic_modal(
                modal,
                categories,
                competitor_fixture,
                competitor["fitur"][0],
                "kompetitor brand %dpx" % width,
            )
            await assert_modal_scroll_path(modal, "kompetitor brand %dpx" % width)
            await assert_modal_round1(page, modal, competitor_fixture, width, "kompetitor brand %dpx" % width)
            await assert_dark_readable(page, modal, "kompetitor brand %dpx" % width)
            await assert_tap_targets(page, "kompetitor modal %dpx" % width)
            await assert_research_ui(page, modal, competitor_brand, competitor["model"], comp_trigger, "kompetitor brand %dpx" % width)
            await page.keyboard.press("Escape")
            await assert_clean(page, errors, "kompetitor %dpx" % width)
            await assert_real_image_fallbacks(page, base, comp_trigger)
            await page.close()
        await browser.close()


async def main():
    fixture = fixtures()
    Handler.catalog = fixture["catalog"]
    Handler.competitor = fixture["competitor_document"]
    Handler.categories = fixture["categories"]
    Handler.research = {"jobs": {}, "log": [], "counter": 0}
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=SITE))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        await run_browser("http://127.0.0.1:%d" % server.server_port, fixture)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    print("PASS verify_product_detail: editor hero-contained nonoverlap 1440/390, mobile AQUA+selected brand switch Samsung, desktop 6 brand, active nav click+keyboard+scrollspy, single visible scrollbar+bottom, grouped provenance, theme settle 350ms, sabotage, legacy/security/performance guards")


if __name__ == "__main__":
    asyncio.run(main())
