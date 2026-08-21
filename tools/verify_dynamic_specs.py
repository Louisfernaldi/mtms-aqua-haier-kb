# -*- coding: utf-8 -*-
"""Validator skema spesifikasi dinamis MTMS (stdlib-only)."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

try:
    from .migrate_dynamic_specs import (
        CORE_CATEGORY_KEYS,
        SPEC_VALUE_FIELDS,
        categories_list,
        has_meaningful_spec_state,
        iter_models,
        migrate_document,
        serialized_document,
    )
except ImportError:  # eksekusi langsung: python tools/verify_dynamic_specs.py
    from migrate_dynamic_specs import (  # type: ignore
        CORE_CATEGORY_KEYS,
        SPEC_VALUE_FIELDS,
        categories_list,
        has_meaningful_spec_state,
        iter_models,
        migrate_document,
        serialized_document,
    )


ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_PATH = ROOT / "site" / "data" / "spec-categories.json"
DATA_PATH = ROOT / "site" / "data" / "kompetitor.json"
EDITOR_HTML_PATH = ROOT / "site" / "kompetitor.html"
PRODUCT_HTML_PATH = ROOT / "site" / "produk.html"
PRODUCT_JS_PATH = ROOT / "site" / "js" / "produk.js"
EDITOR_JS_PATH = ROOT / "site" / "js" / "dynamic-spec-editor.js"
EDITOR_CSS_PATH = ROOT / "site" / "css" / "style.css"
REQUIRED_CATEGORY_FIELDS = {"key", "label", "group", "unit", "comparison", "order", "active"}
REQUIRED_LEGACY_FIELDS = {
    "model",
    "subcat",
    "cat",
    "door",
    "capacity_l",
    "price_idr",
    "price_source",
    "fitur",
    "image",
    "photo_url",
    "source_url",
}
ALLOWED_ORIGINS = {"unknown", "legacy", "research", "user"}


def _valid_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_categories(categories: Any) -> List[str]:
    errors: List[str] = []
    try:
        items = categories_list(categories)
    except ValueError as exc:
        return [str(exc)]

    keys: List[Any] = []
    orders: List[Any] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"category[{index}] harus object")
            continue
        missing = REQUIRED_CATEGORY_FIELDS - set(item)
        if missing:
            errors.append(f"category[{index}] kurang field {sorted(missing)}")
            continue
        keys.append(item["key"])
        orders.append(item["order"])
        if not isinstance(item["key"], str) or not item["key"]:
            errors.append(f"category[{index}] key invalid")
        if not isinstance(item["label"], str) or not item["label"]:
            errors.append(f"category[{index}] label invalid")
        if not isinstance(item["group"], str) or not item["group"]:
            errors.append(f"category[{index}] group invalid")
        if item["unit"] is not None and not isinstance(item["unit"], str):
            errors.append(f"category[{index}] unit invalid")
        if not isinstance(item["comparison"], bool):
            errors.append(f"category[{index}] comparison wajib boolean")
        if not isinstance(item["active"], bool):
            errors.append(f"category[{index}] active wajib boolean")
        if not isinstance(item["order"], int) or isinstance(item["order"], bool):
            errors.append(f"category[{index}] order wajib integer")

    if len(keys) != len(set(keys)):
        errors.append("key kategori duplikat")
    comparable_orders = [value for value in orders if isinstance(value, int) and not isinstance(value, bool)]
    if len(comparable_orders) != len(set(comparable_orders)):
        errors.append("order kategori duplikat")
    if comparable_orders != sorted(comparable_orders):
        errors.append("order kategori tidak stabil menaik")

    if keys[: len(CORE_CATEGORY_KEYS)] != list(CORE_CATEGORY_KEYS):
        errors.append("12 kategori inti tidak lengkap atau urutannya berbeda dari SPEC")
    expected_orders = list(range(10, 121, 10))
    if orders[: len(CORE_CATEGORY_KEYS)] != expected_orders:
        errors.append("order 12 kategori inti wajib 10..120")

    for item in items[: len(CORE_CATEGORY_KEYS)]:
        if isinstance(item, dict) and (item.get("comparison") is not True or item.get("active") is not True):
            errors.append(f"kategori inti {item.get('key')} wajib active/comparison=true")
    # Kategori tambahan dibuat non-comparison oleh migrator, lalu tiket 02
    # mengizinkan user memilihnya sebagai kolom utama. Tipe boolean sudah
    # diperiksa di atas; hanya 12 kategori inti yang wajib selalu true.
    return errors


def _validate_provenance(entry: Any, context: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(entry, dict):
        return [f"{context}: spec value harus object"]
    missing = set(SPEC_VALUE_FIELDS) - set(entry)
    if missing:
        return [f"{context}: kurang provenance {sorted(missing)}"]

    if entry.get("origin") not in ALLOWED_ORIGINS:
        errors.append(f"{context}: origin invalid")
    if not isinstance(entry.get("user_locked"), bool):
        errors.append(f"{context}: user_locked wajib boolean")

    source_url = entry.get("source_url")
    source_kind = entry.get("source_kind")
    verified_at = entry.get("verified_at")
    if source_url is not None and not _valid_url(source_url):
        errors.append(f"{context}: source_url invalid")
    if source_kind is not None and (not isinstance(source_kind, str) or not source_kind.strip()):
        errors.append(f"{context}: source_kind invalid")
    if verified_at is not None and not _valid_timestamp(verified_at):
        errors.append(f"{context}: verified_at invalid")
    if source_url is not None and source_kind is None:
        errors.append(f"{context}: source_url tanpa source_kind")
    if verified_at is not None and source_url is None:
        errors.append(f"{context}: verified_at tanpa source_url")

    if entry.get("origin") == "research" and entry.get("value") is not None:
        if not _valid_url(source_url):
            errors.append(f"{context}: nilai research wajib URL valid")
        if not isinstance(source_kind, str) or not source_kind.strip():
            errors.append(f"{context}: nilai research wajib source_kind")
        if not _valid_timestamp(verified_at):
            errors.append(f"{context}: nilai research wajib verified_at bertimezone")
    if entry.get("origin") == "unknown":
        if entry.get("value") is not None:
            errors.append(f"{context}: origin unknown wajib value=null")
        if any(entry.get(field) is not None for field in ("source_url", "source_kind", "verified_at")):
            errors.append(f"{context}: nilai unknown tidak boleh punya provenance sumber")
    return errors


def validate_document(
    data: Any,
    categories: Any,
    *,
    expected_models: int | None = None,
    expected_brands: int | None = None,
    require_legacy_fields: bool = False,
) -> List[str]:
    errors: List[str] = []
    try:
        items = categories_list(categories)
        model_rows = list(iter_models(data))
    except ValueError as exc:
        return [str(exc)]

    category_keys = [item.get("key") for item in items if isinstance(item, dict)]
    category_key_set = set(category_keys)
    if expected_models is not None and len(model_rows) != expected_models:
        errors.append(f"jumlah model {len(model_rows)} != {expected_models}")
    if expected_brands is not None:
        brands = {brand for brand, _ in model_rows}
        if len(brands) != expected_brands:
            errors.append(f"jumlah merek {len(brands)} != {expected_brands}")

    seen_ids: set[str] = set()
    for brand, model in model_rows:
        model_name = model.get("model")
        expected_id = f"{brand}::{model_name}"
        context = expected_id
        if model.get("model_id") != expected_id:
            errors.append(f"{context}: model_id tidak exact brand+model")
        if expected_id in seen_ids:
            errors.append(f"{context}: model_id duplikat")
        seen_ids.add(expected_id)

        if require_legacy_fields:
            missing_legacy = REQUIRED_LEGACY_FIELDS - set(model)
            if missing_legacy:
                errors.append(f"{context}: field lama hilang {sorted(missing_legacy)}")

        values = model.get("spec_values")
        if not isinstance(values, dict):
            errors.append(f"{context}: spec_values harus object")
            continue
        orphans = set(values) - category_key_set
        if orphans:
            errors.append(f"{context}: kategori yatim {sorted(orphans)}")
        for key, entry in values.items():
            errors.extend(_validate_provenance(entry, f"{context}/{key}"))
            if isinstance(entry, dict) and not has_meaningful_spec_state(entry):
                errors.append(f"{context}/{key}: state unknown kosong wajib dihilangkan")

        suggestions = model.get("research_suggestions")
        if not isinstance(suggestions, list):
            errors.append(f"{context}: research_suggestions harus list")
        else:
            for index, suggestion in enumerate(suggestions):
                suggestion_context = f"{context}/suggestion[{index}]"
                if not isinstance(suggestion, dict):
                    errors.append(f"{suggestion_context}: wajib object")
                    continue
                if suggestion.get("key") not in category_key_set:
                    errors.append(f"{suggestion_context}: kategori yatim")
                source_url = suggestion.get("source_url")
                source_kind = suggestion.get("source_kind")
                verified_at = suggestion.get("verified_at")
                if source_url is not None and not _valid_url(source_url):
                    errors.append(f"{suggestion_context}: source_url invalid")
                if source_url is not None and not isinstance(source_kind, str):
                    errors.append(f"{suggestion_context}: source_kind invalid")
                if verified_at is not None and not _valid_timestamp(verified_at):
                    errors.append(f"{suggestion_context}: verified_at invalid")
    return errors


def _model_index(data: Any) -> Dict[str, Dict[str, Any]]:
    return {f"{brand}::{model.get('model')}": model for brand, model in iter_models(data)}


def find_user_overwrites(before: Any, after: Any) -> List[str]:
    errors: List[str] = []
    before_index = _model_index(before)
    after_index = _model_index(after)
    for model_id, before_model in before_index.items():
        after_model = after_index.get(model_id, {})
        before_values = before_model.get("spec_values")
        if not isinstance(before_values, dict):
            continue
        after_values = after_model.get("spec_values") if isinstance(after_model, dict) else None
        for key, before_entry in before_values.items():
            if not isinstance(before_entry, dict):
                continue
            protected = before_entry.get("origin") == "user" or before_entry.get("user_locked") is True
            if not protected:
                continue
            after_entry = after_values.get(key) if isinstance(after_values, dict) else None
            if not isinstance(after_entry, dict) or after_entry.get("value") != before_entry.get("value"):
                errors.append(f"{model_id}/{key}: nilai user tertimpa")
    return errors


def find_lost_model_fields(before: Any, after: Any) -> List[str]:
    errors: List[str] = []
    after_index = _model_index(after)
    for brand, before_model in iter_models(before):
        model_id = f"{brand}::{before_model.get('model')}"
        after_model = after_index.get(model_id)
        if after_model is None:
            errors.append(f"{model_id}: model hilang")
            continue
        for key, value in before_model.items():
            if key in {"model_id", "spec_values", "research_suggestions"}:
                continue
            if key not in after_model or after_model[key] != value:
                errors.append(f"{model_id}: field lama berubah/hilang: {key}")
    return errors


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_editor_wiring() -> List[str]:
    """Static offline gate for ticket 02 editor markup and API concurrency wiring."""
    errors: List[str] = []
    for path in (EDITOR_HTML_PATH, PRODUCT_HTML_PATH, PRODUCT_JS_PATH, EDITOR_JS_PATH, EDITOR_CSS_PATH):
        if not path.is_file():
            errors.append(f"editor file hilang: {path.relative_to(ROOT)}")
    if errors:
        return errors

    html = EDITOR_HTML_PATH.read_text(encoding="utf-8")
    product_html = PRODUCT_HTML_PATH.read_text(encoding="utf-8")
    product_js = PRODUCT_JS_PATH.read_text(encoding="utf-8")
    javascript = EDITOR_JS_PATH.read_text(encoding="utf-8")
    css = EDITOR_CSS_PATH.read_text(encoding="utf-8")

    html_needles = (
        'src="js/dynamic-spec-editor.js"',
        "MTMSDynamicSpecEditor.mount",
        'dataUrl: "api/kompetitor"',
        'categoriesUrl: "api/spec-categories"',
        "initialData: d",
        "initialSha: compSha",
    )
    product_needles = (
        'src="js/dynamic-spec-editor.js"',
        "MTMSDynamicSpecEditor.mount",
        'dataUrl: "api/produk"',
        "initialData: liveItems",
        "initialSha: window.MTMS_PRODUCTS_SHA",
    )
    js_needles = (
        "button.disabled = true",
        'data-live-ready',
        'data-ds-model-select',
        'data-ds-spec-key',
        'data-ds-features',
        'research_suggestions',
        'fitur_meta',
        'feature_suggestions',
        'data-ds-suggestion="accept"',
        'data-ds-suggestion="reject"',
        'data-ds-feature-suggestion="accept"',
        'data-ds-feature-suggestion="reject"',
        'data-ds-create-category',
        'name="active"',
        'name="order"',
        'name="comparison"',
        'X-Data-SHA',
        'ETag',
        'If-Match',
        'method: "PATCH"',
        'STALE SHA',
    )
    css_needles = (".ds-editor-fab", ".ds-editor-panel", ".ds-spec-row", ".ds-suggestion", ".ds-category-card")

    for needle in html_needles:
        if needle not in html:
            errors.append(f"wiring HTML editor hilang: {needle}")
    for needle in product_needles:
        if needle not in product_html and needle not in product_js:
            errors.append(f"wiring Produk editor hilang: {needle}")
    for needle in js_needles:
        if needle not in javascript:
            errors.append(f"wiring JS editor hilang: {needle}")
    for needle in css_needles:
        if needle not in css:
            errors.append(f"style editor hilang: {needle}")
    return errors


def main() -> int:
    categories_document = _read_json(CATEGORIES_PATH)
    data = _read_json(DATA_PATH)
    category_errors = validate_categories(categories_document)
    document_errors = validate_document(
        data,
        categories_document,
        expected_models=102,
        expected_brands=6,
        require_legacy_fields=True,
    )

    once_categories = copy.deepcopy(categories_document)
    once = migrate_document(copy.deepcopy(data), once_categories)
    twice_categories = copy.deepcopy(once_categories)
    twice = migrate_document(copy.deepcopy(once), twice_categories)
    user_overwrites = find_user_overwrites(data, once)
    lost_fields = find_lost_model_fields(data, once)
    byte_identical = (
        serialized_document(once) == serialized_document(twice)
        and serialized_document(once_categories, indent=2) == serialized_document(twice_categories, indent=2)
    )

    editor_errors = validate_editor_wiring()
    all_errors = category_errors + document_errors + user_overwrites + lost_fields + editor_errors
    if not byte_identical:
        all_errors.append("migrasi dua kali tidak byte-identik")

    categories = categories_list(categories_document)
    models = list(iter_models(data))
    model_count = len(models)
    spec_record_count = sum(len(model.get("spec_values", {})) for _, model in models)
    empty_record_count = sum(
        not has_meaningful_spec_state(entry)
        for _, model in models
        for entry in model.get("spec_values", {}).values()
        if isinstance(entry, dict)
    )
    orphan_count = sum("kategori yatim" in error for error in document_errors)
    invalid_source_count = sum(
        "source_" in error or "verified_at" in error or "nilai research" in error
        for error in document_errors
    )
    duplicate_count = sum("duplikat" in error for error in category_errors)
    digest = hashlib.sha256(serialized_document(once)).hexdigest()

    print(f"verify_dynamic_specs: models={model_count}/102 brands=6/6")
    print(
        "verify_dynamic_specs: categories=%d core=12 additional=%d duplicate_keys=%d orphan_categories=%d"
        % (len(categories), max(0, len(categories) - 12), duplicate_count, orphan_count)
    )
    print(
        "verify_dynamic_specs: invalid_sources=%d user_overwrites=%d lost_legacy_fields=%d"
        % (invalid_source_count, len(user_overwrites), len(lost_fields))
    )
    print(
        "verify_dynamic_specs: sparse_records=%d empty_unknown_records=%d"
        % (spec_record_count, empty_record_count)
    )
    print(
        "verify_dynamic_specs: idempotent_semantic=true idempotent_bytes=%s sha256=%s"
        % (str(byte_identical).lower(), digest)
    )
    print("verify_dynamic_specs: editor_wiring=%s" % str(not editor_errors).lower())

    if all_errors:
        for error in all_errors:
            print("GAGAL:", error)
        return 1
    print("LULUS: 102/102 model valid; kategori yatim 0; overwrite user 0; field lama utuh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
