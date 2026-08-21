# -*- coding: utf-8 -*-
"""Gerbang deterministik staging dan hasil merge riset spesifikasi tiket 03."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple
from urllib.parse import urlparse

try:
    from .migrate_dynamic_specs import CORE_CATEGORY_KEYS, categories_list, iter_models, serialized_document
    from .verify_dynamic_specs import validate_categories, validate_document
except ImportError:  # eksekusi langsung: python tools/verify_spec_research.py
    from migrate_dynamic_specs import CORE_CATEGORY_KEYS, categories_list, iter_models, serialized_document  # type: ignore
    from verify_dynamic_specs import validate_categories, validate_document  # type: ignore


ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = ROOT / "research" / "specs-staging"
CATEGORIES_PATH = ROOT / "site" / "data" / "spec-categories.json"
COMPETITOR_PATH = ROOT / "site" / "data" / "kompetitor.json"
PRODUCT_PATH = ROOT / "site" / "data" / "produk-katalog.json"
SUMMARY_JSON_PATH = STAGING_DIR / "MERGED-SUMMARY.json"
SUMMARY_MD_PATH = ROOT / "evidence" / "spec-research" / "ALL-BRANDS-SUMMARY.md"

COMPETITOR_STAGING_NAMES = ("AQUA", "LG", "MIDEA", "POLYTRON", "SAMSUNG", "SHARP")
STAGING_NAMES = COMPETITOR_STAGING_NAMES + ("AQUA_PRODUCT_EXTRA",)
EXPECTED_COUNTS = {
    "AQUA": 32,
    "LG": 16,
    "MIDEA": 7,
    "POLYTRON": 13,
    "SAMSUNG": 11,
    "SHARP": 23,
    "AQUA_PRODUCT_EXTRA": 10,
}
REQUIRED_RECORD_FIELDS = {
    "model_id",
    "brand",
    "model",
    "research_status",
    "exact_match",
    "checked_urls",
    "specs",
    "additional_specs",
    "unresolved_core",
    "notes",
}
REQUIRED_RESEARCH_VALUE_FIELDS = {"value", "raw_value", "source_url", "source_kind", "verified_at"}
ADDITIONAL_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_CATEGORY_FIELDS = {"key", "label", "group", "unit", "comparison", "order", "active"}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def valid_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_checked_url(value: Any, context: str) -> List[str]:
    """Terima format URL ringkas atau receipt percobaan yang lebih lengkap."""

    if isinstance(value, str):
        return [] if valid_url(value) else [f"{context}: URL invalid"]
    if not isinstance(value, dict):
        return [f"{context}: checked URL harus string atau object"]
    errors: List[str] = []
    required = {"url", "source_kind", "attempt", "outcome", "checked_at"}
    missing = required - set(value)
    if missing:
        return [f"{context}: receipt kurang field {sorted(missing)}"]
    if not valid_url(value.get("url")):
        errors.append(f"{context}: receipt URL invalid")
    if not isinstance(value.get("source_kind"), str) or not value["source_kind"].strip():
        errors.append(f"{context}: receipt source_kind invalid")
    attempt = value.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or not 1 <= attempt <= 2:
        errors.append(f"{context}: receipt attempt wajib 1 atau 2")
    if not isinstance(value.get("outcome"), str) or not value["outcome"].strip():
        errors.append(f"{context}: receipt outcome invalid")
    if not valid_timestamp(value.get("checked_at")):
        errors.append(f"{context}: receipt checked_at wajib bertimezone")
    return errors


def load_staging_documents(staging_dir: Path = STAGING_DIR) -> Dict[str, Any]:
    return {name: read_json(staging_dir / (name + ".json")) for name in STAGING_NAMES}


def flatten_records(documents: Mapping[str, Any], names: Iterable[str] = STAGING_NAMES) -> List[Dict[str, Any]]:
    return [record for name in names for record in documents[name].get("records", [])]


def model_index(document: Any) -> Dict[str, Dict[str, Any]]:
    return {f"{brand}::{model.get('model')}": model for brand, model in iter_models(document)}


def _validate_value(value: Any, context: str, *, additional: bool) -> List[str]:
    errors: List[str] = []
    if not isinstance(value, dict):
        return [f"{context}: value riset harus object"]
    missing = REQUIRED_RESEARCH_VALUE_FIELDS - set(value)
    if missing:
        return [f"{context}: kurang field {sorted(missing)}"]

    normalized = value.get("value")
    if normalized is None or isinstance(normalized, dict):
        errors.append(f"{context}: value wajib terisi dan bukan object")
    if isinstance(normalized, list):
        if not additional or not normalized or any(isinstance(item, (dict, list)) or item is None for item in normalized):
            errors.append(f"{context}: list value hanya boleh nonempty scalar pada additional_specs")
    raw_value = value.get("raw_value")
    if not isinstance(raw_value, str) or not raw_value.strip():
        errors.append(f"{context}: raw_value wajib string nonempty")
    if not valid_url(value.get("source_url")):
        errors.append(f"{context}: source_url wajib http(s) valid")
    if not isinstance(value.get("source_kind"), str) or not value["source_kind"].strip():
        errors.append(f"{context}: source_kind wajib string nonempty")
    if not valid_timestamp(value.get("verified_at")):
        errors.append(f"{context}: verified_at wajib timestamp bertimezone")
    return errors


def validate_research_contract(
    documents: Mapping[str, Any],
    competitor: Any,
    products: Any,
) -> List[str]:
    """Validasi seluruh kontrak staging tanpa memperbaiki atau menebak data."""

    errors: List[str] = []
    all_records: List[Dict[str, Any]] = []
    for name in STAGING_NAMES:
        document = documents.get(name)
        if not isinstance(document, dict):
            errors.append(f"{name}.json: top-level harus object")
            continue
        expected_brand = "AQUA" if name == "AQUA_PRODUCT_EXTRA" else name
        if document.get("brand") != expected_brand:
            errors.append(f"{name}.json: brand {document.get('brand')!r} != {expected_brand!r}")
        if name == "AQUA_PRODUCT_EXTRA" and document.get("scope") != "product_extra":
            errors.append("AQUA_PRODUCT_EXTRA.json: scope wajib product_extra")
        if not valid_timestamp(document.get("researched_at")):
            errors.append(f"{name}.json: researched_at wajib bertimezone")
        records = document.get("records")
        if not isinstance(records, list):
            errors.append(f"{name}.json: records harus list")
            continue
        if document.get("model_count") != EXPECTED_COUNTS[name] or len(records) != EXPECTED_COUNTS[name]:
            errors.append(
                f"{name}.json: model_count/records {document.get('model_count')}/{len(records)} != {EXPECTED_COUNTS[name]}"
            )
        models = [record.get("model") for record in records if isinstance(record, dict)]
        if models != sorted(models):
            errors.append(f"{name}.json: records wajib urut exact model")

        for index, record in enumerate(records):
            context = f"{name}.json/record[{index}]"
            if not isinstance(record, dict):
                errors.append(f"{context}: record harus object")
                continue
            missing = REQUIRED_RECORD_FIELDS - set(record)
            if missing:
                errors.append(f"{context}: kurang field {sorted(missing)}")
                continue
            all_records.append(record)
            model_id = record.get("model_id")
            expected_id = f"{record.get('brand')}::{record.get('model')}"
            context = str(model_id)
            if model_id != expected_id:
                errors.append(f"{context}: model_id bukan exact brand::model")
            if record.get("brand") != expected_brand:
                errors.append(f"{context}: brand record tidak cocok dokumen")
            if not isinstance(record.get("model"), str) or not record["model"]:
                errors.append(f"{context}: model wajib string nonempty")
            if not isinstance(record.get("exact_match"), bool):
                errors.append(f"{context}: exact_match wajib boolean")

            checked_urls = record.get("checked_urls")
            if not isinstance(checked_urls, list) or not checked_urls:
                errors.append(f"{context}: checked_urls wajib list nonempty")
            else:
                for url_index, checked_url in enumerate(checked_urls):
                    errors.extend(validate_checked_url(checked_url, f"{context}/checked_urls[{url_index}]"))
            notes = record.get("notes")
            if not isinstance(notes, list) or any(not isinstance(note, str) or not note.strip() for note in notes):
                errors.append(f"{context}: notes wajib list string nonempty")

            specs = record.get("specs")
            additional = record.get("additional_specs")
            if not isinstance(specs, dict) or not isinstance(additional, dict):
                errors.append(f"{context}: specs dan additional_specs wajib object")
                continue
            unknown_core = set(specs) - set(CORE_CATEGORY_KEYS)
            if unknown_core:
                errors.append(f"{context}: core key tidak diizinkan {sorted(unknown_core)}")
            bad_additional = [
                key for key in additional
                if key in CORE_CATEGORY_KEYS or not isinstance(key, str) or not ADDITIONAL_KEY_RE.fullmatch(key)
            ]
            if bad_additional:
                errors.append(f"{context}: additional key invalid {sorted(map(str, bad_additional))}")

            exact = record.get("exact_match") is True
            if not exact and (specs or additional):
                errors.append(f"{context}: exact_match=false wajib specs/additional_specs kosong")
            if exact and not specs and not additional:
                errors.append(f"{context}: exact match tanpa nilai riset")

            unresolved = record.get("unresolved_core")
            expected_unresolved = [key for key in CORE_CATEGORY_KEYS if key not in specs]
            if unresolved != expected_unresolved:
                errors.append(f"{context}: unresolved_core bukan exact complement terurut")

            expected_status = "unresolved" if not exact else ("complete" if not expected_unresolved else "partial")
            if record.get("research_status") != expected_status:
                errors.append(
                    f"{context}: research_status {record.get('research_status')!r} != {expected_status!r}"
                )

            for key, value in specs.items():
                errors.extend(_validate_value(value, f"{context}/specs/{key}", additional=False))
            for key, value in additional.items():
                errors.extend(_validate_value(value, f"{context}/additional_specs/{key}", additional=True))

            if "capacity_unlabelled_l" in additional and ({"gross_capacity_l", "net_capacity_l"} & set(specs)):
                errors.append(f"{context}: capacity_unlabelled_l tidak boleh dipromosikan ke gross/net core")
            if "dimensions_unlabelled" in additional and ({"width_mm", "height_mm", "depth_mm"} & set(specs)):
                errors.append(f"{context}: dimensions_unlabelled tidak boleh dipromosikan ke dimensi core")

    all_ids = [record.get("model_id") for record in all_records]
    duplicate_ids = sorted(model_id for model_id, count in Counter(all_ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"staging: duplicate identity {duplicate_ids}")
    if len(all_ids) != 112 or len(set(all_ids)) != 112:
        errors.append(f"staging: union unique {len(set(all_ids))}/112; records={len(all_ids)}")

    competitor_ids = set(model_index(competitor))
    competitor_staging_ids = {record["model_id"] for record in flatten_records(documents, COMPETITOR_STAGING_NAMES)}
    if len(competitor_ids) != 102:
        errors.append(f"kompetitor fallback: unique identity {len(competitor_ids)}/102")
    missing_competitor = sorted(competitor_ids - competitor_staging_ids)
    extra_competitor = sorted(competitor_staging_ids - competitor_ids)
    if missing_competitor or extra_competitor:
        errors.append(f"kompetitor staging bukan exact 102/102; missing={missing_competitor} extra={extra_competitor}")

    product_ids = set(model_index(products))
    aqua_competitor_ids = {model_id for model_id in competitor_ids if model_id.startswith("AQUA::")}
    expected_product_extra = product_ids - aqua_competitor_ids
    product_extra_ids = {record["model_id"] for record in documents["AQUA_PRODUCT_EXTRA"].get("records", [])}
    if len(product_ids) != 42:
        errors.append(f"produk fallback: unique identity {len(product_ids)}/42")
    if len(expected_product_extra) != 10 or product_extra_ids != expected_product_extra:
        errors.append(
            "produk extra bukan exact set difference 10; missing=%s extra=%s"
            % (sorted(expected_product_extra - product_extra_ids), sorted(product_extra_ids - expected_product_extra))
        )
    expected_union = competitor_ids | product_extra_ids
    if set(all_ids) != expected_union or len(expected_union) != 112:
        errors.append("staging: denominator union target wajib exact 112 unique")
    return errors


def validate_research_categories(categories: Any, documents: Mapping[str, Any]) -> List[str]:
    """Validasi kategori riset sebagai suffix deterministik registry global tunggal."""

    if not isinstance(categories, dict):
        return ["research categories: wrapper wajib object"]
    errors: List[str] = []
    if "research_categories" in categories:
        errors.append("research_categories sibling tidak boleh ada")
    try:
        items = categories_list(categories)
    except ValueError as exc:
        return errors + [str(exc)]
    explicit = sorted({
        key
        for record in flatten_records(documents)
        if record.get("exact_match") is True
        for key in record.get("additional_specs", {})
    })
    additional_items = items[-len(explicit):] if explicit else []
    keys = []
    leading_items = items[:-len(explicit)] if explicit else items
    leading_orders = [
        item.get("order") for item in leading_items
        if isinstance(item, dict) and isinstance(item.get("order"), int) and not isinstance(item.get("order"), bool)
    ]
    first_order = max(leading_orders, default=120) + 10
    for offset, item in enumerate(additional_items):
        index = len(leading_items) + offset
        context = f"spec_categories[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{context}: wajib object")
            continue
        missing = REQUIRED_CATEGORY_FIELDS - set(item)
        if missing:
            errors.append(f"{context}: kurang field {sorted(missing)}")
            continue
        keys.append(item.get("key"))
        if item.get("group") != "Tambahan":
            errors.append(f"{context}: group wajib Tambahan")
        if item.get("comparison") is not False:
            errors.append(f"{context}: comparison wajib false")
        if item.get("active") is not True:
            errors.append(f"{context}: active wajib true")
        if item.get("unit") != "-":
            errors.append(f"{context}: unit wajib -")
        if item.get("order") != first_order + offset * 10:
            errors.append(f"{context}: order tidak stabil")
    if keys != explicit:
        errors.append(f"suffix spec_categories bukan exact explicit additional keys; got={keys} expected={explicit}")
    if len(keys) != len(set(keys)):
        errors.append("kategori riset tambahan key duplikat")
    return errors


def validate_research_additional_output(data: Any, categories: Any) -> List[str]:
    """Tolak sibling lama dan validasi additional di field kanonis model."""

    try:
        registry = categories_list(categories)
    except ValueError as exc:
        return [str(exc)]
    additional_keys = {
        item.get("key") for item in registry[len(CORE_CATEGORY_KEYS):]
        if isinstance(item, dict)
    }
    errors: List[str] = []
    for brand, model in iter_models(data):
        context = f"{brand}::{model.get('model')}"
        for forbidden in ("research_additional_values", "research_additional_suggestions"):
            if forbidden in model:
                errors.append(f"{context}: sibling {forbidden} tidak boleh ada")
        values = model.get("spec_values")
        if not isinstance(values, dict):
            continue
        for key in additional_keys & set(values):
            entry = values[key]
            if isinstance(entry, dict) and entry.get("origin") == "research":
                errors.extend(_validate_value(entry, f"{context}/{key}", additional=True))
        suggestions = model.get("research_suggestions")
        if not isinstance(suggestions, list):
            continue
        for index, suggestion in enumerate(suggestions):
            if not isinstance(suggestion, dict):
                continue
            if suggestion.get("key") in additional_keys and suggestion.get("status") not in {"pending", "accepted", "rejected"}:
                errors.append(f"{context}/suggestion[{index}]: status invalid")
    return errors


def research_entry(value: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "value": value["value"],
        "source_url": value["source_url"],
        "source_kind": value["source_kind"],
        "verified_at": value["verified_at"],
        "origin": "research",
        "user_locked": False,
        "raw_value": value["raw_value"],
    }


def suggestion_matches(suggestion: Any, key: str, value: Mapping[str, Any]) -> bool:
    if not isinstance(suggestion, dict) or suggestion.get("key") != key:
        return False
    fields = ("value", "source_url", "source_kind", "verified_at", "raw_value")
    return all(canonical_json(suggestion.get(field)) == canonical_json(value.get(field)) for field in fields)


def research_value_matches(entry: Any, value: Mapping[str, Any]) -> bool:
    if not isinstance(entry, dict):
        return False
    expected = research_entry(value)
    return all(canonical_json(entry.get(field)) == canonical_json(expected[field]) for field in expected)


def _application_report_for_target(
    target_name: str,
    data: Any,
    records: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    index = model_index(data)
    applied_core: Counter[str] = Counter()
    applied_additional: Counter[str] = Counter()
    applied_sources: Counter[str] = Counter()
    exact_models = 0
    skipped_non_exact = 0
    conflicts = 0
    pending_suggestions = 0
    protected_preserved = 0

    for record in records:
        model_id = record["model_id"]
        model = index.get(model_id)
        if model is None:
            errors.append(f"{target_name}/{model_id}: target record hilang")
            continue
        if record["exact_match"] is not True:
            skipped_non_exact += 1
            leaked = [
                key for key, entry in model.get("spec_values", {}).items()
                if isinstance(entry, dict) and entry.get("origin") == "research"
            ]
            if leaked:
                errors.append(f"{target_name}/{model_id}: non-exact mendapat research values {sorted(leaked)}")
            continue
        exact_models += 1
        values = model.get("spec_values") if isinstance(model.get("spec_values"), dict) else {}
        suggestions = model.get("research_suggestions") if isinstance(model.get("research_suggestions"), list) else []
        for group_name, staged_values in (("core", record["specs"]), ("additional", record["additional_specs"])):
            for key, staged_value in staged_values.items():
                if group_name == "core":
                    entry = values.get(key)
                    group_suggestions = suggestions
                else:
                    entry = values.get(key)
                    group_suggestions = suggestions
                if research_value_matches(entry, staged_value):
                    if group_name == "core":
                        applied_core[key] += 1
                    else:
                        applied_additional[key] += 1
                    applied_sources[staged_value["source_kind"]] += 1
                    continue
                matches = [item for item in group_suggestions if suggestion_matches(item, key, staged_value)]
                if matches:
                    conflicts += 1
                    if any(item.get("status") == "pending" for item in matches):
                        pending_suggestions += 1
                    continue
                protected = isinstance(entry, dict) and (
                    entry.get("origin") == "user" or entry.get("user_locked") is True
                )
                same_value = isinstance(entry, dict) and canonical_json(entry.get("value")) == canonical_json(staged_value["value"])
                if protected and same_value:
                    protected_preserved += 1
                    continue
                errors.append(f"{target_name}/{model_id}/{key}: exact research tidak applied atau menjadi suggestion")

    applied_total = sum(applied_core.values()) + sum(applied_additional.values())
    return {
        "target_models": len(records),
        "exact_models": exact_models,
        "skipped_non_exact": skipped_non_exact,
        "applied_values": {
            "total": applied_total,
            "core": dict(sorted(applied_core.items())),
            "additional": dict(sorted(applied_additional.items())),
            "source_kind": dict(sorted(applied_sources.items())),
        },
        "conflicts": conflicts,
        "suggestions_pending": pending_suggestions,
        "protected_preserved": protected_preserved,
    }, errors


def build_application_report(
    documents: Mapping[str, Any],
    competitor: Any,
    products: Any,
) -> Tuple[Dict[str, Any], List[str]]:
    competitor_records = flatten_records(documents, COMPETITOR_STAGING_NAMES)
    product_records = documents["AQUA"]["records"] + documents["AQUA_PRODUCT_EXTRA"]["records"]
    competitor_report, competitor_errors = _application_report_for_target(
        "kompetitor", competitor, competitor_records
    )
    product_report, product_errors = _application_report_for_target("produk-katalog", products, product_records)
    return {
        "targets": {
            "kompetitor": competitor_report,
            "produk-katalog": product_report,
        },
        "totals": {
            "target_model_applications": competitor_report["target_models"] + product_report["target_models"],
            "exact_model_applications": competitor_report["exact_models"] + product_report["exact_models"],
            "skipped_non_exact": competitor_report["skipped_non_exact"] + product_report["skipped_non_exact"],
            "applied_values": competitor_report["applied_values"]["total"] + product_report["applied_values"]["total"],
            "conflicts": competitor_report["conflicts"] + product_report["conflicts"],
            "suggestions_pending": competitor_report["suggestions_pending"] + product_report["suggestions_pending"],
            "protected_preserved": competitor_report["protected_preserved"] + product_report["protected_preserved"],
        },
    }, competitor_errors + product_errors


def build_summary(
    documents: Mapping[str, Any],
    application: Mapping[str, Any],
    output_payloads: Mapping[str, bytes],
    staging_dir: Path = STAGING_DIR,
) -> Dict[str, Any]:
    records = flatten_records(documents)
    statuses = Counter(record["research_status"] for record in records)
    exact = sum(record["exact_match"] is True for record in records)
    per_brand: Dict[str, Any] = {}
    for name in STAGING_NAMES:
        rows = documents[name]["records"]
        per_brand[name] = {
            "records": len(rows),
            "exact": sum(row["exact_match"] is True for row in rows),
            "partial": sum(row["research_status"] == "partial" for row in rows),
            "unresolved": sum(row["research_status"] == "unresolved" for row in rows),
        }
    staging_files = []
    for name in STAGING_NAMES:
        path = staging_dir / (name + ".json")
        staging_files.append({
            "file": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
            "sha256": sha256_path(path),
        })
    return {
        "schema_version": 1,
        "research": {
            "denominator_unique": len({record["model_id"] for record in records}),
            "records": len(records),
            "exact": exact,
            "complete": statuses["complete"],
            "partial": statuses["partial"],
            "unresolved": statuses["unresolved"],
            "duplicate_identity": len(records) - len({record["model_id"] for record in records}),
            "record_missing": 112 - len({record["model_id"] for record in records}),
            "per_source_file": per_brand,
        },
        "application": application,
        "staging_files": staging_files,
        "outputs": {
            name: {"sha256": sha256_bytes(payload), "bytes": len(payload)}
            for name, payload in sorted(output_payloads.items())
        },
    }


def summary_markdown(summary: Mapping[str, Any]) -> str:
    research = summary["research"]
    totals = summary["application"]["totals"]
    lines = [
        "# All-Brands Specification Research Merge Summary",
        "",
        "Snapshot deterministik tiket 03; seluruh sumber berasal dari tujuh JSON staging lokal.",
        "",
        "## Denominator Riset",
        "",
        f"- Unique target: **{research['denominator_unique']}/112**",
        f"- Exact / partial / unresolved: **{research['exact']} / {research['partial']} / {research['unresolved']}**",
        f"- Complete: **{research['complete']}**",
        f"- Duplicate identity / record missing: **{research['duplicate_identity']} / {research['record_missing']}**",
        "",
        "## Hasil Apply Lokal",
        "",
        f"- Target model applications: **{totals['target_model_applications']}** (Kompetitor 102 + Produk 42)",
        f"- Exact applications / skipped non-exact: **{totals['exact_model_applications']} / {totals['skipped_non_exact']}**",
        f"- Applied values: **{totals['applied_values']}**",
        f"- Conflicts / pending suggestions: **{totals['conflicts']} / {totals['suggestions_pending']}**",
        f"- Protected values preserved: **{totals['protected_preserved']}**",
        "- Single semantic contract: 12 kategori inti tetap pertama; 29 kategori tambahan di-append ke `spec_categories`, dan seluruh nilai sparse hidup di `spec_values`.",
    ]
    for target_name, target in summary["application"]["targets"].items():
        values = target["applied_values"]
        lines.extend([
            "",
            f"### {target_name}",
            "",
            f"- Models / exact / skipped: {target['target_models']} / {target['exact_models']} / {target['skipped_non_exact']}",
            f"- Applied / conflicts / suggestions: {values['total']} / {target['conflicts']} / {target['suggestions_pending']}",
            "",
            "| Core key | Applied |",
            "|---|---:|",
        ])
        lines.extend(f"| `{key}` | {count} |" for key, count in values["core"].items())
        lines.extend(["", "| Additional key | Applied |", "|---|---:|"])
        lines.extend(f"| `{key}` | {count} |" for key, count in values["additional"].items())
        lines.extend(["", "| Source kind | Applied |", "|---|---:|"])
        lines.extend(f"| `{key}` | {count} |" for key, count in values["source_kind"].items())
    lines.extend(["", "## SHA-256 Outputs", "", "| Output | Bytes | SHA-256 |", "|---|---:|---|"])
    for name, state in summary["outputs"].items():
        lines.append(f"| `{name}` | {state['bytes']} | `{state['sha256']}` |")
    lines.extend([
        "",
        "Non-exact records tidak diterapkan. Notes tidak pernah menjadi fitur atau spesifikasi; hanya `specs` dan `additional_specs` eksplisit yang diproses.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    documents = load_staging_documents()
    categories = read_json(CATEGORIES_PATH)
    competitor = read_json(COMPETITOR_PATH)
    products = read_json(PRODUCT_PATH)
    errors = validate_research_contract(documents, competitor, products)
    errors.extend(validate_categories(categories))
    errors.extend(validate_research_categories(categories, documents))
    errors.extend(validate_document(competitor, categories, expected_models=102, expected_brands=6, require_legacy_fields=True))
    errors.extend(validate_document(products, categories, expected_models=42, expected_brands=1))
    errors.extend(validate_research_additional_output(competitor, categories))
    errors.extend(validate_research_additional_output(products, categories))
    application, application_errors = build_application_report(documents, competitor, products)
    errors.extend(application_errors)

    outputs = {
        CATEGORIES_PATH.relative_to(ROOT).as_posix(): serialized_document(categories, indent=2),
        COMPETITOR_PATH.relative_to(ROOT).as_posix(): serialized_document(competitor, indent=1),
        PRODUCT_PATH.relative_to(ROOT).as_posix(): serialized_document(products, indent=2),
    }
    expected_summary = build_summary(documents, application, outputs)
    expected_json = serialized_document(expected_summary, indent=2)
    expected_md = summary_markdown(expected_summary).encode("utf-8")
    if not SUMMARY_JSON_PATH.is_file() or SUMMARY_JSON_PATH.read_bytes() != expected_json:
        errors.append("MERGED-SUMMARY.json hilang atau tidak cocok dengan output saat ini")
    if not SUMMARY_MD_PATH.is_file() or SUMMARY_MD_PATH.read_bytes() != expected_md:
        errors.append("ALL-BRANDS-SUMMARY.md hilang atau tidak cocok dengan output saat ini")

    research = expected_summary["research"]
    totals = application["totals"]
    print(
        "verify_spec_research: staging=7/7 competitor_targets=102/102 denominator=%d/112 duplicate=%d missing=%d"
        % (research["denominator_unique"], research["duplicate_identity"], research["record_missing"])
    )
    print(
        "verify_spec_research: exact=%d partial=%d unresolved=%d skipped_non_exact=%d"
        % (research["exact"], research["partial"], research["unresolved"], totals["skipped_non_exact"])
    )
    print(
        "verify_spec_research: applied_values=%d conflicts=%d suggestions_pending=%d protected=%d"
        % (
            totals["applied_values"],
            totals["conflicts"],
            totals["suggestions_pending"],
            totals["protected_preserved"],
        )
    )
    for name, state in expected_summary["outputs"].items():
        print(f"verify_spec_research: sha256 {name}={state['sha256']}")
    if errors:
        for error in errors:
            print("GAGAL:", error)
        return 1
    print("LULUS: staging konsisten; exact-only merge terbukti; user lock utuh; kategori tambahan tidak yatim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
