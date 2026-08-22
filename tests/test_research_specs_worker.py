import hashlib
import json
import threading
import time
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from unittest.mock import patch
from urllib import error as urllib_error
from urllib import request as urllib_request

from tools.research_specs import (
    CasStaleError,
    FetchResult,
    run_worker,
    make_suggestion_id,
    stable_scalar,
    main,
)


JOB_ID = "a" * 32
MODEL_ID = "ACME::RFG-217"


class InMemoryGithub:
    def __init__(self, queue, data_files):
        self.queue = deepcopy(queue)
        self.data_files = deepcopy(data_files)
        self.write_calls = []

    def _sha(self, data):
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()

    def read_queue(self):
        return deepcopy(self.queue), self._sha(self.queue)

    def write_queue(self, data, base_sha, message):
        if base_sha != self._sha(self.queue):
            raise CasStaleError("stale")
        self.queue = deepcopy(data)
        new_sha = self._sha(self.queue)
        self.write_calls.append((base_sha, new_sha, message))
        return new_sha

    def read_data(self, path):
        payload = deepcopy(self.data_files.get(path, {}))
        return payload, self._sha(payload)


class _LocalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = self.server.page_map.get(self.path)
        if self.path == "/slow":
            time.sleep(3)
        if body is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *_args, **_kwargs):
        return


class TestResearchSpecsWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.happy_body = """
            <html><body>
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Product",
              "name": "ACME::RFG-217",
              "numberOfDoors": "3",
              "netCapacity": "217 L",
              "width": "550 mm"
            }
            </script>
            </body></html>
        """.strip()

        cls.wrong_body = """
            <html><body>
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Product",
              "name": "ACME::RFG-777",
              "numberOfDoors": "4"
            }
            </script>
            </body></html>
        """.strip()

        cls.list_body = """
            <html><body>
            <script type="application/ld+json">
            [
              {"@type":"Product","name":"OTHER","numberOfDoors":1},
              {"@type":"Product","name":"ACME::RFG-217","width": "555 mm"}
            ]
            </script>
            </body></html>
        """.strip()

        cls.huge_body = "<html>" + ("x" * 4000) + "</html>"
        cls.page_map = {
            "/happy": cls.happy_body,
            "/wrong": cls.wrong_body,
            "/list": cls.list_body,
            "/huge": cls.huge_body,
            "/slow": "<html><body>slow</body></html>",
        }
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _LocalHandler)
        cls.server.page_map = cls.page_map
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=2)

    def setUp(self):
        queue = {"schema_version": 1, "jobs": {JOB_ID: self._base_job()}}
        data_files = {
            "kompetitor.json": {
                "brands": [
                    {
                        "brand_id": "ACME",
                        "models": [
                            {
                                "model_id": MODEL_ID,
                                "spec_values": {
                                    "net_capacity_l": {"value": 200},
                                    "door_count": {"value": 3},
                                },
                            }
                        ],
                    }
                ]
            },
            "produk-katalog.json": [
                {
                    "model_id": MODEL_ID,
                    "spec_values": {
                        "net_capacity_l": {"value": 200},
                        "door_count": {"value": 3},
                    },
                }
            ],
        }
        self.github = InMemoryGithub(queue, data_files)

    def _base_job(self):
        return {
            "job_id": JOB_ID,
            "model_id": MODEL_ID,
            "target": "produk",
            "status": "queued",
            "sources": [],
            "attempts": 0,
            "max_attempts": 2,
            "requested_at": "2026-01-01T00:00:00Z",
        }

    def _base_url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def _now(self):
        return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def _fetch_local(self, url: str, timeout_s: float, max_bytes: int) -> FetchResult:
        request = urllib_request.Request(url, headers={"User-Agent": "mtms-test"})
        try:
            with urllib_request.urlopen(request, timeout=timeout_s) as response:
                status = response.getcode()
                body = response.read(max_bytes + 1)
                if status >= 400:
                    return FetchResult(False, status, None, "http_error", None)
                if len(body) > max_bytes:
                    return FetchResult(False, status, None, "too_large", "SOURCE_TOO_LARGE")
                return FetchResult(True, status, body, "ok", None)
        except urllib_error.HTTPError as exc:
            return FetchResult(False, exc.code, None, "http_error", None)
        except (urllib_error.URLError, TimeoutError, OSError):
            return FetchResult(False, None, None, "fetch_error", None)

    def _run(
        self,
        *,
        status="queued",
        sources=None,
        attempts=0,
        max_attempts=2,
        target="produk",
        max_bytes=2000000,
    ):
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        job["status"] = status
        job["sources"] = sources if sources is not None else []
        job["attempts"] = attempts
        job["max_attempts"] = max_attempts
        job["target"] = target
        self.github.queue = queue
        self.github.queue["jobs"][JOB_ID].update(job)
        return run_worker(
            JOB_ID,
            MODEL_ID,
            github=self.github,
            fetch_fn=self._fetch_local,
            now_fn=self._now,
            timeout_s=1.0,
            max_bytes=max_bytes,
        )

    def test_happy_page_completed_with_valid_candidates(self):
        payload = self.github.read_data("produk-katalog.json")[0]
        payload[0]["spec_values"] = {"net_capacity_l": {"value": 200}}
        self.github.data_files["produk-katalog.json"] = payload
        code = self._run(
            sources=[{"url": self._base_url("/happy"), "source_kind": "model_page"}],
            target="produk",
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        self.assertEqual(job["status"], "completed")
        self.assertIsNone(job["error_code"])
        candidates = {c["key"]: c for c in job["candidates"]}
        self.assertEqual(candidates["door_count"]["value"], 3)
        self.assertEqual(candidates["net_capacity_l"]["value"], 217)
        self.assertEqual(candidates["width_mm"]["value"], 550)
        self.assertEqual(candidates["door_count"]["status"], "pending")
        self.assertEqual(len(candidates["door_count"]["suggestion_id"]), 64)
        self.assertTrue(candidates["door_count"]["verified_at"].endswith("Z"))

    def test_wrong_model_becomes_unresolved(self):
        code = self._run(
            sources=[{"url": self._base_url("/wrong"), "source_kind": "model_page"}],
            target="produk",
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        self.assertEqual(job["status"], "unresolved")
        self.assertEqual(job["error_code"], "MODEL_NOT_CONFIRMED")

    def test_http_404_source_receipt(self):
        code = self._run(
            sources=[{"url": self._base_url("/missing"), "source_kind": "model_page"}],
            attempts=1,
            max_attempts=2,
            target="produk",
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        self.assertEqual(job["sources"][0]["outcome"], "http_error")
        self.assertEqual(job["sources"][0]["http_status"], 404)

    def test_slow_fetch_becomes_fetch_error(self):
        code = self._run(
            sources=[{"url": self._base_url("/slow"), "source_kind": "model_page"}],
            target="produk",
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        self.assertEqual(job["sources"][0]["outcome"], "fetch_error")

    def test_oversized_body_marks_source_too_large(self):
        code = self._run(
            sources=[{"url": self._base_url("/huge"), "source_kind": "model_page"}],
            target="produk",
            attempts=0,
            max_attempts=2,
            max_bytes=10,
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        self.assertEqual(job["sources"][0]["outcome"], "too_large")
        self.assertEqual(job["sources"][0]["error_code"], "SOURCE_TOO_LARGE")

    def test_completed_job_is_skipped_and_not_written(self):
        self._run(
            status="completed",
            sources=[{"url": self._base_url("/happy"), "source_kind": "model_page"}],
            target="produk",
        )
        before = len(self.github.write_calls)
        code = self._run(
            status="completed",
            sources=[{"url": self._base_url("/happy"), "source_kind": "model_page"}],
            target="produk",
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(self.github.write_calls), before)

    def test_all_failed_sources_and_attempts_reached_fails_job(self):
        code = self._run(
            sources=[{"url": self._base_url("/missing"), "source_kind": "model_page"}],
            attempts=2,
            max_attempts=2,
            target="produk",
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["error_code"], "SOURCE_FETCH_FAILED")

    def test_observed_filter_drops_matching_candidates(self):
        job_data = {
            "net_capacity_l": {"value": 200},
            "door_count": {"value": 3},
        }
        payload = self.github.read_data("produk-katalog.json")[0]
        payload[0]["spec_values"] = job_data
        self.github.data_files["produk-katalog.json"] = payload
        code = self._run(
            sources=[{"url": self._base_url("/happy"), "source_kind": "model_page"}],
            target="produk",
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        keys = {c["key"] for c in job["candidates"]}
        self.assertNotIn("door_count", keys)
        self.assertIn("net_capacity_l", keys)

    def test_suggestion_id_is_stable(self):
        value = make_suggestion_id(MODEL_ID, "door_count", 3, self._base_url("/happy"))
        repeated = make_suggestion_id(MODEL_ID, "door_count", 3, self._base_url("/happy"))
        expected = hashlib.sha256(
            json.dumps(
                ["suggestion-v2", MODEL_ID, "door_count", stable_scalar(3), self._base_url("/happy")],
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(value, repeated)
        self.assertEqual(value, expected)

    def test_cli_without_token_returns_two(self):
        with patch.dict("os.environ", {}, clear=True):
            exit_code = main(
                ["--job-id", JOB_ID, "--model-id", MODEL_ID],
            )
        self.assertEqual(exit_code, 2)

    def test_bonus_mixed_ok_and_fail_still_completed(self):
        payload = self.github.read_data("produk-katalog.json")[0]
        payload[0]["spec_values"] = {"net_capacity_l": {"value": 200}}
        self.github.data_files["produk-katalog.json"] = payload
        self.github.queue["jobs"][JOB_ID]["attempts"] = 0
        code = self._run(
            sources=[
                {"url": self._base_url("/happy"), "source_kind": "model_page"},
                {"url": self._base_url("/missing"), "source_kind": "model_page"},
            ],
            target="produk",
        )
        queue = self.github.read_queue()[0]
        job = queue["jobs"][JOB_ID]
        self.assertEqual(code, 0)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["candidates"][0]["source_url"], self._base_url("/happy"))
        self.assertEqual(len(job["candidates"]), 3)
        keys = {c["key"] for c in job["candidates"]}
        self.assertEqual(keys, {"door_count", "net_capacity_l", "width_mm"})


if __name__ == "__main__":
    unittest.main()
