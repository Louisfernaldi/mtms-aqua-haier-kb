"""Worker CLI + module for research specs jobs."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib import error as url_error
from urllib import request as url_request
from urllib.parse import urljoin, urlparse


SCRIPT_LD_JSON_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class FetchResult:
    ok: bool
    status: int | None
    body: bytes | None
    outcome: str
    error_code: str | None = None


class CasStaleError(RuntimeError):
    """Raised when queue write is rejected because of stale SHA."""


class RealGithubAdapter:
    def __init__(
        self,
        token: str,
        repo: str,
        queue_branch: str = "research-queue",
        queue_path: str = "research-jobs.json",
        data_branch: str = "main",
        api_base: str = "https://api.github.com",
    ) -> None:
        self.token = token
        self.repo = repo
        self.queue_branch = queue_branch
        self.queue_path = queue_path
        self.data_branch = data_branch
        self.api_base = api_base.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "mtms-research-specs-worker",
        }

    def read_queue(self) -> tuple[dict, str]:
        path = f"/repos/{self.repo}/contents/{self.queue_path}"
        url = f"{self.api_base}{path}?ref={self.queue_branch}"
        body = self._request("GET", url)
        data = json.loads(body.decode("utf-8"))
        sha = data["sha"]
        content = data.get("content", "")
        decoded = base64.b64decode(content)
        return json.loads(decoded.decode("utf-8")), sha

    def write_queue(self, data: dict, base_sha: str, message: str) -> str:
        path = f"/repos/{self.repo}/contents/{self.queue_path}"
        url = f"{self.api_base}{path}"
        payload = json.dumps(
            {
                "message": message,
                "content": base64.b64encode(
                    json.dumps(data, ensure_ascii=False).encode("utf-8")
                ).decode("ascii"),
                "branch": self.queue_branch,
                "sha": base_sha,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        body = self._request("PUT", url, payload)
        data = json.loads(body.decode("utf-8"))
        return data["content"]["sha"]

    def read_data(self, path: str) -> tuple[dict, str]:
        encoded_path = path.replace(" ", "%20")
        url = (
            f"{self.api_base}/repos/{self.repo}/contents/{encoded_path}"
            f"?ref={self.data_branch}"
        )
        body = self._request("GET", url)
        data = json.loads(body.decode("utf-8"))
        sha = data["sha"]
        content = data.get("content", "")
        decoded = base64.b64decode(content)
        return json.loads(decoded.decode("utf-8")), sha

    def _request(self, method: str, url: str, body: bytes | None = None) -> bytes:
        req = url_request.Request(url, data=body, method=method, headers=self._headers)
        try:
            with url_request.urlopen(req, timeout=8.0) as resp:
                resp_body = resp.read()
                return resp_body
        except url_error.HTTPError as ex:
            status = getattr(ex, "code", None)
            if status in (409, 422):
                raise CasStaleError(f"GitHub API stale write: {status}") from ex
            content = ex.read() if hasattr(ex, "read") else b""
            raise RuntimeError(f"GitHub API error {status}: {content[:200]!r}") from ex
        except url_error.URLError as ex:
            raise RuntimeError(f"GitHub request failed: {ex}") from ex


def stable_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return f"boolean:{str(value).lower()}"
    if isinstance(value, int):
        return f"number:{value}"
    if isinstance(value, float):
        if value.is_integer():
            return f"number:{int(value)}"
        return f"number:{value}"
    return f"string:{str(value)}"


def make_suggestion_id(model_id: str, key: str, value, source_url: str | None) -> str:
    payload = [
        "suggestion-v2",
        model_id,
        key,
        stable_scalar(value),
        source_url if source_url else None,
    ]
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _now_iso(now_fn: callable) -> str:
    now = now_fn()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _get_job(data: dict, job_id: str) -> dict | None:
    jobs = data.get("jobs", {})
    return copy.deepcopy(jobs.get(job_id))

def _set_job(data: dict, job_id: str, job: dict) -> None:
    if "jobs" not in data or not isinstance(data["jobs"], dict):
        data["jobs"] = {}
    data["jobs"][job_id] = job


def _snapshot_observed(model: dict | None) -> dict:
    observed: dict = {}
    if not model:
        return observed
    spec_values = model.get("spec_values") or {}
    if not isinstance(spec_values, dict):
        return observed
    for key, item in spec_values.items():
        if isinstance(item, dict):
            observed[key] = item.get("value")
        else:
            observed[key] = item
    return observed


def _find_competitor_model(data: dict, model_id: str) -> dict | None:
    brands = data.get("brands")
    if not isinstance(brands, list):
        return None
    for brand in brands:
        models = brand.get("models") if isinstance(brand, dict) else None
        if not isinstance(models, list):
            continue
        for model in models:
            if isinstance(model, dict) and model.get("model_id") == model_id:
                return model
    return None


def _find_product_model(data: list, model_id: str) -> dict | None:
    if not isinstance(data, list):
        return None
    for model in data:
        if isinstance(model, dict) and model.get("model_id") == model_id:
            return model
    return None


def _target_path(target: str) -> str | None:
    if target == "kompetitor":
        return "kompetitor.json"
    if target == "produk":
        return "produk-katalog.json"
    return None


def _extract_numeric(value):
    if isinstance(value, (int, float, bool)):
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, int):
            return value
        if value.is_integer():
            return int(value)
        return value
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.fullmatch(r"\s*([+-]?\d[\d\.,\s]*)(?:\s*[A-Za-z]{1,6})?\s*", text)
    if not match:
        return None

    number = match.group(1).replace(" ", "")
    if not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)*", number):
        return None

    if "," in number and "." in number:
        if number.rfind(",") > number.rfind("."):
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif "," in number:
        if number.count(",") > 1:
            number = number.replace(",", "")
        else:
            left, right = number.rsplit(",", 1)
            if len(right) == 3 and left and left != "+" and left != "-":
                number = number.replace(",", "")
            else:
                number = number.replace(",", ".")
    elif "." in number:
        if number.count(".") > 1:
            number = number.replace(".", "")
        else:
            left, right = number.rsplit(".", 1)
            if len(right) == 3 and left and left != "+" and left != "-":
                number = number.replace(".", "")
    try:
        if "." in number:
            return float(number)
        return int(number)
    except ValueError:
        return None


def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return None
    if isinstance(value, (int, float, bool)):
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
        return value
    normalized = str(value).strip()
    if normalized == "":
        return None
    parsed = _extract_numeric(normalized)
    if isinstance(parsed, str):
        return parsed[:1000]
    if parsed is not None:
        return parsed
    return normalized[:1000]


def _iter_product_nodes(payload):
    if isinstance(payload, dict):
        if _is_product_type(payload):
            yield payload
        for value in payload.values():
            if isinstance(value, (dict, list)):
                yield from _iter_product_nodes(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_product_nodes(item)


def _is_product_type(node: dict) -> bool:
    type_value = node.get("@type")
    if isinstance(type_value, str):
        types = [type_value]
    elif isinstance(type_value, list):
        types = [str(v) for v in type_value if isinstance(v, str)]
    else:
        return False
    return any(v.lower() == "product" for v in types)


def _model_match(
    model_id: str,
    html_lower: str,
    product_node: dict | None = None,
) -> bool:
    mid = model_id.lower()
    part = model_id.split("::", 1)[-1].lower() if "::" in model_id else model_id.lower()
    if mid in html_lower:
        return True
    # Halaman resmi lazim menyebut nama model polos tanpa awalan merek;
    # URL sumber sudah dipatok allowlist resmi per merek, jadi ini aman.
    if part and part in html_lower:
        return True
    if not isinstance(product_node, dict):
        return False
    for key in ("sku", "model", "mpn", "name"):
        value = product_node.get(key)
        if not isinstance(value, str):
            continue
        candidate = value.strip().lower()
        if candidate and candidate in (mid, part):
            return True
    return False


def _collect_candidates(product_node: dict, source_kind: str, source_url: str) -> list[dict]:
    alias_map = {
        "form_factor": ["formFactor", "refrigeratorType"],
        "door_count": ["numberOfDoors"],
        "freezer_position": ["freezerPosition"],
        "gross_capacity_l": ["grossCapacity", "grossCapacityLitres", "capacity"],
        "net_capacity_l": ["netCapacity", "netCapacityLitres", "storageVolume"],
        "width_mm": ["width"],
        "height_mm": ["height"],
        "depth_mm": ["depth"],
        "rated_power_w": ["powerRating", "ratedPower"],
        "compressor_type": ["compressorType"],
        "cooling_system": ["coolingSystem"],
        "defrost_type": ["defrostType"],
    }
    out = []
    if not isinstance(product_node, dict):
        return out
    for key, aliases in alias_map.items():
        raw = None
        for alias in aliases:
            if alias in product_node and product_node[alias] is not None:
                raw = product_node[alias]
                break
        if raw is None:
            continue
        normalized = _normalize_value(raw)
        if normalized is None:
            continue
        out.append({"key": key, "value": normalized, "source_url": source_url, "source_kind": source_kind})
    return out


def default_fetch_fn(url: str, timeout_s: float, max_bytes: int) -> FetchResult:
    if not url.lower().startswith("https://"):
        return FetchResult(False, None, None, "not_html", "SOURCE_NOT_HTML")

    current = url
    redirects = 0
    while True:
        try:
            req = url_request.Request(current, method="GET", headers={
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/126.0.0.0 Safari/537.36"),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "id-ID,id;q=0.9",
            })
            with url_request.urlopen(req, timeout=timeout_s) as resp:
                status = getattr(resp, "status", None) or getattr(resp, "code", None)
                if status in (301, 302, 303, 307, 308) and redirects < 2:
                    location = resp.headers.get("Location")
                    if location:
                        redirects += 1
                        current = urljoin(current, location)
                        continue
                if status is None:
                    return FetchResult(False, None, None, "http_error", None)
                if status >= 400:
                    return FetchResult(False, status, None, "http_error", None)
                content_type = (resp.headers.get("Content-Type") or "").lower()
                if not content_type.startswith("text/html"):
                    return FetchResult(False, status, None, "not_html", "SOURCE_NOT_HTML")
                body = resp.read(max_bytes + 1)
                if len(body) > max_bytes:
                    return FetchResult(False, status, None, "too_large", "SOURCE_TOO_LARGE")
                return FetchResult(True, status, body, "ok", None)
        except url_error.HTTPError as exc:
            code = getattr(exc, "code", None)
            return FetchResult(False, code, None, "http_error", None)
        except (url_error.URLError, TimeoutError, OSError) as exc:
            if hasattr(exc, "reason"):
                _ = exc.reason  # placeholder for clarity
            return FetchResult(False, None, None, "fetch_error", None)


def _build_receipt(url: str, result: FetchResult, now_fn) -> dict:
    return {
        "url": url,
        "outcome": result.outcome,
        "http_status": result.status,
        "checked_at": _now_iso(now_fn),
        "error_code": result.error_code,
    }


def _write_with_retries(
    github: RealGithubAdapter,
    job_id: str,
    updater,
    max_attempts: int = 3,
    terminal: bool = False,
) -> int:
    for attempt in range(max_attempts):
        queue, sha = github.read_queue()
        current = _get_job(queue, job_id)
        if not current:
            print("JOB_NOT_FOUND", file=sys.stderr)
            return 1
        if not terminal and current.get("status") != "queued":
            print("JOB_ALREADY_TAKEN", file=sys.stderr)
            return 0
        if terminal and current.get("status") != "running":
            return 0
        updated = updater(current)
        _set_job(queue, job_id, updated)
        try:
            github.write_queue(queue, sha, f"research job {job_id} update")
            return 0
        except CasStaleError:
            continue
        except Exception as exc:
            print("GITHUB_WRITE_FAILED", file=sys.stderr)
            return 1
    print("GITHUB_QUEUE_CAS_STALE", file=sys.stderr)
    return 1


def run_worker(
    job_id: str,
    model_id: str,
    github,
    fetch_fn,
    now_fn,
    timeout_s: float = 8.0,
    max_bytes: int = 2000000,
) -> int:
    queue, queue_sha = github.read_queue()
    job = _get_job(queue, job_id)
    if not job:
        print("JOB_NOT_FOUND", file=sys.stderr)
        return 1

    if job.get("model_id") != model_id:
        print("MODEL_MISMATCH", file=sys.stderr)
        return 1

    # Klaim ulang: status queued, ATAU running yang tersangkut karena semua
    # sumber gagal pada percobaan sebelumnya (kode LAST_FETCH_FAILED) dan
    # kuota attempts-nya masih ada. Ini pasangan dari izin dispatch-ulang di
    # functions/api/research.js (dispatchIsEligible).
    retryable = (
        job.get("status") == "running"
        and job.get("error_code") == "LAST_FETCH_FAILED"
        and int(job.get("attempts", 0)) < int(job.get("max_attempts", 2))
    )
    if job.get("status") != "queued" and not retryable:
        print("SKIP_ALREADY_PROCESSED")
        return 0

    def claim_updater(current: dict) -> dict:
        copy_job = copy.deepcopy(current)
        copy_job["status"] = "running"
        copy_job["started_at"] = _now_iso(now_fn)
        copy_job["attempts"] = min(
            int(current.get("attempts", 0)) + 1,
            int(current.get("max_attempts", 2)),
        )
        copy_job["updated_at"] = _now_iso(now_fn)
        return copy_job

    if _write_with_retries(github, job_id, claim_updater, max_attempts=3, terminal=False) != 0:
        return 1

    queue, queue_sha = github.read_queue()
    job = _get_job(queue, job_id)
    if not job:
        print("JOB_NOT_FOUND", file=sys.stderr)
        return 1

    target_path = _target_path(job.get("target", "produk"))
    if target_path is None:
        print("INVALID_TARGET", file=sys.stderr)
        return 1

    observed_map: dict = {}
    try:
        target_data, _ = github.read_data(target_path)
    except Exception:
        target_data = {}
    if job.get("target") == "kompetitor":
        model_obj = _find_competitor_model(target_data, model_id)
    else:
        model_obj = _find_product_model(target_data, model_id)
    observed_map = _snapshot_observed(model_obj)

    receipts = []
    candidates = []
    model_confirmed = False
    sources = job.get("sources") if isinstance(job.get("sources"), list) else []
    for source in sources[:2]:
        source_url = source.get("url") if isinstance(source, dict) else None
        source_kind = source.get("source_kind") if isinstance(source, dict) else None
        if not source_url:
            result = FetchResult(False, None, None, "fetch_error", "SOURCE_INVALID_URL")
        else:
            result = fetch_fn(source_url, timeout_s=timeout_s, max_bytes=max_bytes)
        checked_at = _now_iso(now_fn)
        receipt = {
            "url": source_url,
            "outcome": result.outcome,
            "http_status": result.status,
            "checked_at": checked_at,
        }
        if result.error_code:
            receipt["error_code"] = result.error_code
        receipts.append(receipt)
        if not result.ok or result.body is None:
            continue
        html = result.body.decode("utf-8", errors="ignore")
        html_lower = html.lower()
        source_candidates = []
        for script_content in SCRIPT_LD_JSON_RE.findall(html):
            try:
                payload = json.loads(script_content.strip())
            except json.JSONDecodeError:
                continue
            for product in _iter_product_nodes(payload):
                if not _is_product_type(product):
                    continue
                if _model_match(model_id, html_lower, product):
                    model_confirmed = True
                    source_candidates.extend(_collect_candidates(product, source_kind, source_url))
        for item in source_candidates:
            value = item["value"]
            key = item["key"]
            candidate = {
                "key": key,
                "value": value,
                "observed_value": observed_map.get(key),
                "source_url": source_url,
                "source_kind": source_kind,
                "verified_at": checked_at,
                "status": "pending",
                "suggestion_id": make_suggestion_id(model_id, key, value, source_url),
            }
            candidates.append(candidate)

    seen = set()
    deduped = []
    for candidate in candidates:
        dedup_key = (candidate["key"], candidate["value"], candidate["source_url"])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        if len(deduped) >= 100:
            break
        deduped.append(candidate)

    all_fetch_failed = all(item.get("outcome") != "ok" for item in receipts)
    final_attempts = int(job.get("attempts", 0))
    max_attempts = int(job.get("max_attempts", 2))

    if model_confirmed:
        final_status = "completed"
        final_error = None
        should_finish = True
    elif all_fetch_failed and final_attempts >= max_attempts:
        final_status = "failed"
        final_error = "SOURCE_FETCH_FAILED"
        should_finish = True
    elif all_fetch_failed:
        final_status = "running"
        final_error = "LAST_FETCH_FAILED"
        should_finish = False
    else:
        final_status = "unresolved"
        final_error = "MODEL_NOT_CONFIRMED"
        should_finish = True

    writable_candidates = []
    for cand in deduped:
        if cand["status"] != "pending":
            continue
        if cand["observed_value"] is None or cand["value"] != cand["observed_value"]:
            writable_candidates.append(cand)

    now_ts = _now_iso(now_fn)

    def terminal_updater(current: dict) -> dict:
        copy_job = copy.deepcopy(current)
        copy_job["status"] = final_status
        copy_job["error_code"] = final_error
        copy_job["updated_at"] = now_ts
        copy_job["sources"] = receipts
        copy_job["candidates"] = writable_candidates
        if should_finish:
            copy_job["finished_at"] = now_ts
        else:
            copy_job.pop("finished_at", None)
        return copy_job

    terminal_result = _write_with_retries(github, job_id, terminal_updater, max_attempts=3, terminal=True)
    if terminal_result != 0:
        return terminal_result
    print(f"{final_status}:{job_id}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Research specs worker")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--model-id", required=True)
    args = parser.parse_args(argv)

    token = os.environ.get("MTMS_RESEARCH_DATA_TOKEN")
    if not token:
        print("MTMS_RESEARCH_DATA_TOKEN is required", file=sys.stderr)
        return 2

    github = RealGithubAdapter(
        token=token,
        repo=os.environ.get("RESEARCH_DATA_REPO", "Louisfernaldi/mtms-aqua-haier-kb-data"),
        queue_branch=os.environ.get("RESEARCH_BRANCH", "research-queue"),
        queue_path=os.environ.get("RESEARCH_JOBS_PATH", "research-jobs.json"),
        data_branch=os.environ.get("DATA_BRANCH", "main"),
        api_base=os.environ.get("GITHUB_API", "https://api.github.com"),
    )

    timeout_s = float(os.environ.get("RESEARCH_FETCH_TIMEOUT_S", "8.0"))
    return run_worker(
        args.job_id,
        args.model_id,
        github=github,
        fetch_fn=default_fetch_fn,
        now_fn=lambda: datetime.now(timezone.utc),
        timeout_s=timeout_s,
    )


if __name__ == "__main__":
    sys.exit(main())
