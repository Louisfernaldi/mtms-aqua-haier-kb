#!/usr/bin/env python3
"""Browser E2E lokal untuk pagar XSS dan stale-save tiket 02."""

from __future__ import annotations

import base64
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SHA = "a" * 40
MARKER = "T02_PAYLOAD_MARKER"
EVENT_CODE = "window.__T02_SECURITY_MARKER=(window.__T02_SECURITY_MARKER||0)+1"
INJECTED_ID = "t02-injected-element"
HTML_PAYLOAD = (
    MARKER
    + '"><img id="'
    + INJECTED_ID
    + '" src="/x-t02" onerror="'
    + EVENT_CODE
    + '">'
)
QUOTE_PAYLOAD = (
    "kutipan ' tunggal dan \" ganda </textarea><img id=\""
    + INJECTED_ID
    + "-quote\" src=\"/x-t02\" onerror=\""
    + EVENT_CODE
    + '\">'
)
IMAGE_PAYLOAD = (
    'assets/favicon.svg?T02_IMG_QUOTE=" onerror="'
    + EVENT_CODE
    + '" data-t02="'
)
JAVASCRIPT_URL = "javascript:" + EVENT_CODE
DATA_IMAGE_URL = "data:image/png;base64,iVBORw0KGgo="
PREVIEW_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def dynamic_fields() -> dict:
    return {
        "model_id": "AQUA::" + HTML_PAYLOAD,
        "spec_values": {
            "width_mm": {
                "value": QUOTE_PAYLOAD,
                "source_url": JAVASCRIPT_URL,
                "source_kind": "adversarial_fixture",
                "verified_at": "2026-08-21T12:00:00+07:00",
                "origin": "research",
                "user_locked": False,
            }
        },
        "research_suggestions": [],
        "fitur_meta": {
            "source_url": JAVASCRIPT_URL,
            "source_kind": "adversarial_fixture",
            "verified_at": "2026-08-21T12:00:00+07:00",
            "origin": "research",
            "user_locked": False,
        },
        "feature_suggestions": [],
    }


def product_payload() -> list[dict]:
    product = {
        "brand": "AQUA",
        "model": HTML_PAYLOAD,
        "kategori": QUOTE_PAYLOAD,
        "group": "Top Mount",
        "varian": [QUOTE_PAYLOAD],
        "kapasitas_gross": 300,
        "kapasitas_nett": 280,
        "range": "250-300",
        "material": QUOTE_PAYLOAD,
        "daya_watt": "50",
        "garansi_tahun": "12",
        "flags": [QUOTE_PAYLOAD],
        "benefit": QUOTE_PAYLOAD,
        "fitur": [QUOTE_PAYLOAD],
        "foto": IMAGE_PAYLOAD,
        "foto_list": [IMAGE_PAYLOAD],
        "source_url": JAVASCRIPT_URL,
        "photo_url": JAVASCRIPT_URL,
    }
    product.update(dynamic_fields())
    return [product]


def competitor_payload() -> dict:
    model = {
        "model": HTML_PAYLOAD,
        "cat": "TM",
        "subcat": "TM",
        "capacity_l": 300,
        "price_idr": 123456,
        "fitur": [QUOTE_PAYLOAD],
        "image": DATA_IMAGE_URL,
        "photo_url": JAVASCRIPT_URL,
        "source_url": JAVASCRIPT_URL,
    }
    model.update(dynamic_fields())
    return {
        "brands": [{"brand": "AQUA", "model_count": 1, "models": [model]}],
        "groups": [{"aqua": HTML_PAYLOAD, "competitors": {}}],
    }


class SecurityHandler(SimpleHTTPRequestHandler):
    competitor_gets = 0
    competitor_puts = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def log_message(self, _format: str, *_args) -> None:
        return

    def send_json(self, payload, status: int = 200, with_sha: bool = True) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if with_sha:
            self.send_header("ETag", '"' + SHA + '"')
            self.send_header("X-Data-SHA", SHA)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - API bawaan http.server
        path = urlsplit(self.path).path
        if path == "/api/produk":
            self.send_json(product_payload())
            return
        if path == "/api/kompetitor":
            type(self).competitor_gets += 1
            self.send_json(competitor_payload())
            return
        if path == "/api/spec-categories":
            categories = json.loads((SITE / "data" / "spec-categories.json").read_text(encoding="utf-8"))
            self.send_json(categories)
            return
        if path == "/api/foto":
            self.send_json({"files": []}, with_sha=False)
            return
        super().do_GET()

    def do_PUT(self) -> None:  # noqa: N802 - API bawaan http.server
        path = urlsplit(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        if path == "/api/kompetitor":
            type(self).competitor_puts += 1
            self.send_json({"error": "stale SHA fixture"}, status=412, with_sha=False)
            return
        self.send_json({"error": "write tidak diizinkan di verifier"}, status=405, with_sha=False)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def dom_security_state(page: Page) -> dict:
    return page.evaluate(
        """
        () => {
          const marker = "__T02_SECURITY_MARKER";
          const eventNames = ["onerror", "onload", "onclick", "onmouseover", "onfocus"];
          const injectedHandlers = Array.from(document.querySelectorAll("*")).filter((element) =>
            eventNames.some((name) => String(element.getAttribute(name) || "").includes(marker))
          ).length;
          const javascriptUrls = Array.from(document.querySelectorAll("[href], [src], [action], [formaction]"))
            .filter((element) => ["href", "src", "action", "formaction"].some((name) =>
              /^\\s*javascript:/i.test(String(element.getAttribute(name) || ""))
            )).length;
          return {
            marker: window.__T02_SECURITY_MARKER,
            injectedElements: document.querySelectorAll('[id^="t02-injected-element"]').length,
            injectedHandlers,
            javascriptUrls
          };
        }
        """
    )


def assert_secure_dom(page: Page, label: str) -> None:
    state = dom_security_state(page)
    require(state["marker"] == 0, f"{label}: marker event berubah menjadi {state['marker']}")
    require(state["injectedElements"] == 0, f"{label}: elemen payload berhasil diinjeksi")
    require(state["injectedHandlers"] == 0, f"{label}: event handler payload ditemukan")
    require(state["javascriptUrls"] == 0, f"{label}: javascript URL masuk ke DOM")
    require(MARKER in page.locator("body").inner_text(), f"{label}: payload teks tidak benar-benar dirender")


def wait_for_ready(page: Page, selector: str) -> None:
    page.locator(selector).wait_for(state="visible", timeout=15_000)
    page.wait_for_timeout(100)


def run_browser(base_url: str) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_init_script(
            """
            window.__T02_SECURITY_MARKER = 0;
            window.addEventListener("beforeunload", function () {
              try {
                sessionStorage.setItem(
                  "t02-live-ready-before-reload",
                  String(window.MTMS_COMPETITOR_LIVE_READY)
                );
              } catch (_error) {}
            });
            """
        )
        page = context.new_page()
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        page.goto(base_url + "/produk.html", wait_until="domcontentloaded")
        wait_for_ready(page, ".pk-card")
        malicious_card = page.locator(".pk-card").filter(has_text=MARKER)
        require(malicious_card.count() == 1, "Produk: kartu payload live tidak tampil tepat satu")
        malicious_card.click()
        wait_for_ready(page, '.pk-modal.open[data-mtms-product-detail="true"]')
        assert_secure_dom(page, "Produk detail")

        close = page.locator('.pk-modal.open[data-mtms-product-detail="true"] .pk-modal-close')
        if close.is_visible():
            close.click()
        editor = page.locator('.ds-editor-fab[data-live-ready="true"]')
        editor.wait_for(state="visible", timeout=15_000)
        editor.click()
        wait_for_ready(page, '#ds-editor-shell:not([hidden])')
        assert_secure_dom(page, "Produk dynamic editor")

        # Jalur fallback overlay sengaja diuji terpisah: skrip editor dikosongkan
        # supaya Edit kolom jatuh ke overlay lama tanpa error resource di console.
        context.route(
            "**/js/dynamic-spec-editor.js",
            lambda route: route.fulfill(status=200, content_type="application/javascript", body=""),
        )

        page.goto(base_url + "/kompetitor.html", wait_until="domcontentloaded")
        trigger = page.locator(".comp-detail-trigger").filter(has_text=MARKER)
        trigger.wait_for(state="visible", timeout=15_000)
        require(trigger.count() == 1, "Kompetitor: kartu payload live tidak tampil tepat satu")
        require(
            trigger.locator('.comp-thumb-missing').count() == 1,
            "Kompetitor: stored data:image tidak ditolak dari elemen gambar",
        )
        require(
            page.locator('img.comp-thumb[src^="data:"]').count() == 0,
            "Kompetitor: stored data:image masuk ke DOM",
        )
        trigger.click()
        wait_for_ready(page, '.pk-modal.open[data-mtms-product-detail="true"]')
        assert_secure_dom(page, "Kompetitor detail")

        # Gerbang XSS harus benar-benar tanpa error browser. Status HTTP 412
        # pada langkah berikutnya dicatat Chromium sebagai resource error,
        # sehingga bukti stale-save dipisahkan dari gerbang payload ini.
        require(not page_errors, "payload page error: " + " | ".join(page_errors))
        require(not console_errors, "payload console error: " + " | ".join(console_errors))
        page_errors.clear()
        console_errors.clear()

        page.locator('.pk-modal.open[data-mtms-product-detail="true"] .pk-modal-close').click()
        page.locator(".comp-edit").filter(has_text="Edit").first.click()
        wait_for_ready(page, ".comp-edit-overlay")
        image_input = page.locator("#cef_image")
        original_image_value = image_input.input_value()
        page.locator("#cef_file_image").set_input_files(
            {"name": "preview.png", "mimeType": "image/png", "buffer": PREVIEW_PNG}
        )
        page.locator("#cef_up_image").click()
        page.wait_for_function(
            "document.querySelector('#cef_prev_image').src.startsWith('data:image/png;base64,')"
        )
        require(
            image_input.input_value() == original_image_value,
            "Preview lokal: data URL ikut tersimpan ke input URL Gambar",
        )
        image_input.fill("assets/kompetitor/preview-safe.png")
        before_gets = SecurityHandler.competitor_gets
        with page.expect_navigation(wait_until="domcontentloaded", timeout=15_000):
            page.locator("#cef_save").click()
        page.wait_for_function("window.MTMS_COMPETITOR_LIVE_READY === true", timeout=15_000)
        require(SecurityHandler.competitor_puts == 1, "412: payload stale tidak boleh di-retry")
        require(SecurityHandler.competitor_gets > before_gets, "412: halaman tidak memuat ulang data live")
        require(
            page.evaluate("sessionStorage.getItem('t02-live-ready-before-reload')") == "false",
            "412: liveReady belum false ketika reload dimulai",
        )
        assert_secure_dom(page, "Kompetitor setelah reload 412")

        require(not page_errors, "page error: " + " | ".join(page_errors))
        unexpected_console = [
            message for message in console_errors
            if "412 (Precondition Failed)" not in message
        ]
        require(not unexpected_console, "console error tak terduga: " + " | ".join(unexpected_console))
        context.close()
        browser.close()


def main() -> int:
    SecurityHandler.competitor_gets = 0
    SecurityHandler.competitor_puts = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), SecurityHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        run_browser(base_url)
    except Exception as exc:
        print(f"GAGAL: {exc}")
        return 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print(
        "LULUS browser security E2E: img-onerror/quote/javascript URL jadi teks/ditolak; "
        "stored data:image ditolak, preview lokal tidak tersimpan, marker=0, "
        "injected element/event=0, payload console error=0, PUT stale=1 tanpa retry, "
        "liveReady=false sebelum reload dan reload GET terbukti"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
