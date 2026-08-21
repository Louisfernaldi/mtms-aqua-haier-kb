# -*- coding: utf-8 -*-
"""Merge aman dan idempoten dari staging riset ke fallback lokal tiket 03."""

from __future__ import annotations

import argparse
import copy
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence, Tuple

try:
    from .migrate_dynamic_specs import CORE_CATEGORY_KEYS, categories_list, iter_models, migrate_document, serialized_document
    from .verify_dynamic_specs import find_user_overwrites, validate_categories, validate_document
    from .verify_spec_research import (
        CATEGORIES_PATH,
        COMPETITOR_PATH,
        COMPETITOR_STAGING_NAMES,
        PRODUCT_PATH,
        ROOT,
        STAGING_DIR,
        SUMMARY_JSON_PATH,
        SUMMARY_MD_PATH,
        build_application_report,
        build_summary,
        canonical_json,
        flatten_records,
        load_staging_documents,
        model_index,
        read_json,
        research_entry,
        suggestion_matches,
        summary_markdown,
        validate_research_additional_output,
        validate_research_categories,
        validate_research_contract,
    )
except ImportError:  # eksekusi langsung: python tools/apply_spec_research.py
    from migrate_dynamic_specs import CORE_CATEGORY_KEYS, categories_list, iter_models, migrate_document, serialized_document  # type: ignore
    from verify_dynamic_specs import find_user_overwrites, validate_categories, validate_document  # type: ignore
    from verify_spec_research import (  # type: ignore
        CATEGORIES_PATH,
        COMPETITOR_PATH,
        COMPETITOR_STAGING_NAMES,
        PRODUCT_PATH,
        ROOT,
        STAGING_DIR,
        SUMMARY_JSON_PATH,
        SUMMARY_MD_PATH,
        build_application_report,
        build_summary,
        canonical_json,
        flatten_records,
        load_staging_documents,
        model_index,
        read_json,
        research_entry,
        suggestion_matches,
        summary_markdown,
        validate_research_additional_output,
        validate_research_categories,
        validate_research_contract,
    )


def _human_label(key: str) -> str:
    return " ".join(word[:1].upper() + word[1:] for word in key.replace("-", " ").replace("_", " ").split())


def ensure_additional_categories(categories: Any, records: Sequence[Dict[str, Any]]) -> None:
    """Append kategori riset tambahan ke satu registry global ``spec_categories``."""

    if not isinstance(categories, dict):
        raise ValueError("categories research wajib wrapper object")
    items = categories_list(categories)
    explicit = sorted({
        key
        for record in records
        if record.get("exact_match") is True
        for key in record.get("additional_specs", {})
    })
    existing: Dict[str, Dict[str, Any]] = {
        item.get("key"): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("key"), str)
    }
    raw_research = categories.get("research_categories")
    if isinstance(raw_research, list):
        for item in raw_research:
            if isinstance(item, dict) and isinstance(item.get("key"), str):
                existing.setdefault(item["key"], item)
    retained = [
        item for item in items
        if not isinstance(item, dict) or item.get("key") not in explicit
    ]

    orders = [
        item.get("order") for item in retained
        if isinstance(item, dict) and isinstance(item.get("order"), int) and not isinstance(item.get("order"), bool)
    ]
    next_order = max(orders, default=120) + 10
    additional_categories = []
    for key in explicit:
        prior = existing.get(key, {})
        additional_categories.append({
            "key": key,
            "label": prior.get("label") or _human_label(key),
            "group": "Tambahan",
            "unit": "-",
            "comparison": False,
            "order": next_order + len(additional_categories) * 10,
            "active": True,
        })
    items[:] = retained + additional_categories
    categories.pop("research_categories", None)


def _is_user_owned(entry: Any) -> bool:
    return isinstance(entry, dict) and (
        entry.get("origin") == "user" or entry.get("user_locked") is True
    )


def _fold_legacy_research_state(data: Any) -> Any:
    """Satukan sibling tiket 03 lama ke field kanonis tanpa kehilangan edit user."""

    prepared = copy.deepcopy(data)
    for brand, model in iter_models(prepared):
        context = f"{brand}::{model.get('model')}"
        values = model.get("spec_values")
        if values is None:
            values = {}
            model["spec_values"] = values
        if not isinstance(values, dict):
            raise ValueError(f"{context}: spec_values harus object")
        additional_values = model.pop("research_additional_values", None)
        if additional_values is not None and not isinstance(additional_values, dict):
            raise ValueError(f"{context}: research_additional_values harus object")
        for key, legacy_entry in (additional_values or {}).items():
            current = values.get(key)
            if current is None:
                values[key] = copy.deepcopy(legacy_entry)
                continue
            current_owned = _is_user_owned(current)
            legacy_owned = _is_user_owned(legacy_entry)
            if current_owned and legacy_owned and canonical_json(current.get("value")) != canonical_json(legacy_entry.get("value")):
                raise ValueError(f"{context}/{key}: dua nilai user lama berbeda; tidak aman memilih otomatis")
            if legacy_owned and not current_owned:
                values[key] = copy.deepcopy(legacy_entry)

        suggestions = model.get("research_suggestions")
        if suggestions is None:
            suggestions = []
            model["research_suggestions"] = suggestions
        if not isinstance(suggestions, list) or not all(isinstance(item, dict) for item in suggestions):
            raise ValueError(f"{context}: research_suggestions harus list of object")
        additional_suggestions = model.pop("research_additional_suggestions", None)
        if additional_suggestions is not None and (
            not isinstance(additional_suggestions, list)
            or not all(isinstance(item, dict) for item in additional_suggestions)
        ):
            raise ValueError(f"{context}: research_additional_suggestions harus list of object")
        known = {canonical_json(item) for item in suggestions}
        for suggestion in additional_suggestions or []:
            serialized = canonical_json(suggestion)
            if serialized not in known:
                suggestions.append(copy.deepcopy(suggestion))
                known.add(serialized)
    return prepared


def _suggestion(key: str, staged: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "key": key,
        "value": copy.deepcopy(staged["value"]),
        "source_url": staged["source_url"],
        "source_kind": staged["source_kind"],
        "verified_at": staged["verified_at"],
        "origin": "research",
        "raw_value": staged["raw_value"],
        "status": "pending",
    }


def _append_suggestion_once(
    suggestions: List[Dict[str, Any]],
    key: str,
    staged: Mapping[str, Any],
) -> None:
    if any(suggestion_matches(item, key, staged) for item in suggestions):
        return
    suggestions.append(_suggestion(key, staged))


def _merge_value(
    values: MutableMapping[str, Any],
    suggestions: List[Dict[str, Any]],
    key: str,
    staged: Mapping[str, Any],
) -> None:
    existing = values.get(key)
    protected = isinstance(existing, dict) and (
        existing.get("origin") == "user" or existing.get("user_locked") is True
    )
    existing_value = existing.get("value") if isinstance(existing, dict) else None
    same_value = isinstance(existing, dict) and canonical_json(existing_value) == canonical_json(staged["value"])

    if protected:
        if not same_value:
            _append_suggestion_once(suggestions, key, staged)
        return
    if existing is None or same_value:
        values[key] = research_entry(staged)
        return
    _append_suggestion_once(suggestions, key, staged)


def apply_research_records(
    data: Any,
    categories: Any,
    records: Sequence[Dict[str, Any]],
) -> Any:
    """Apply exact records ke clone data; non-exact dan notes selalu diabaikan."""

    prepared = _fold_legacy_research_state(data)
    result = migrate_document(prepared, copy.deepcopy(categories))
    index = model_index(result)
    missing = sorted(record["model_id"] for record in records if record["model_id"] not in index)
    if missing:
        raise ValueError(f"target model riset hilang: {missing}")

    for record in records:
        if record.get("exact_match") is not True:
            continue
        model = index[record["model_id"]]
        values = model.setdefault("spec_values", {})
        suggestions = model.setdefault("research_suggestions", [])
        for key, staged in record["specs"].items():
            _merge_value(values, suggestions, key, staged)
        for key, staged in record["additional_specs"].items():
            _merge_value(values, suggestions, key, staged)

    category_order = [item["key"] for item in categories_list(categories)]
    for _, model in iter_models(result):
        values = model.get("spec_values", {})
        model["spec_values"] = {
            key: values[key]
            for key in category_order
            if key in values
        }
        model.pop("research_additional_values", None)
        model.pop("research_additional_suggestions", None)
    return result


def apply_bundle(
    competitor: Any,
    products: Any,
    categories: Any,
    documents: Mapping[str, Any],
) -> Tuple[Any, Any, Any]:
    """Kembalikan (kompetitor, produk, kategori) final tanpa menulis berkas."""

    final_categories = copy.deepcopy(categories)
    all_records = flatten_records(documents)
    ensure_additional_categories(final_categories, all_records)
    competitor_records = flatten_records(documents, COMPETITOR_STAGING_NAMES)
    product_records = documents["AQUA"]["records"] + documents["AQUA_PRODUCT_EXTRA"]["records"]
    final_competitor = apply_research_records(competitor, final_categories, competitor_records)
    final_products = apply_research_records(products, final_categories, product_records)
    return final_competitor, final_products, final_categories


def _write_if_changed(path: Path, payload: bytes) -> bool:
    if path.exists() and path.read_bytes() == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return True


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validasi hasil in-memory tanpa menulis")
    args = parser.parse_args(argv)

    documents = load_staging_documents(STAGING_DIR)
    categories = read_json(CATEGORIES_PATH)
    competitor = read_json(COMPETITOR_PATH)
    products = read_json(PRODUCT_PATH)

    errors = validate_research_contract(documents, competitor, products)
    if errors:
        for error in errors:
            print("GAGAL STAGING:", error)
        print("STOP: staging inkonsisten; tidak ada output yang ditulis")
        return 1

    try:
        final_competitor, final_products, final_categories = apply_bundle(
            competitor, products, categories, documents
        )
    except ValueError as exc:
        print("GAGAL APPLY:", exc)
        print("STOP: tidak ada output yang ditulis")
        return 1

    errors.extend(validate_categories(final_categories))
    errors.extend(validate_research_categories(final_categories, documents))
    errors.extend(validate_document(
        final_competitor,
        final_categories,
        expected_models=102,
        expected_brands=6,
        require_legacy_fields=True,
    ))
    errors.extend(validate_document(final_products, final_categories, expected_models=42, expected_brands=1))
    errors.extend(validate_research_additional_output(final_competitor, final_categories))
    errors.extend(validate_research_additional_output(final_products, final_categories))
    errors.extend(find_user_overwrites(competitor, final_competitor))
    errors.extend(find_user_overwrites(products, final_products))
    application, application_errors = build_application_report(
        documents, final_competitor, final_products
    )
    errors.extend(application_errors)
    if errors:
        for error in errors:
            print("GAGAL APPLY:", error)
        print("STOP: hasil in-memory tidak memenuhi kontrak; tidak ada output yang ditulis")
        return 1

    output_payloads = {
        CATEGORIES_PATH.relative_to(ROOT).as_posix(): serialized_document(final_categories, indent=2),
        COMPETITOR_PATH.relative_to(ROOT).as_posix(): serialized_document(final_competitor, indent=1),
        PRODUCT_PATH.relative_to(ROOT).as_posix(): serialized_document(final_products, indent=2),
    }
    summary = build_summary(documents, application, output_payloads)
    summary_json = serialized_document(summary, indent=2)
    summary_md = summary_markdown(summary).encode("utf-8")

    if args.check:
        changed = [
            name for name, payload in output_payloads.items()
            if not (ROOT / name).exists() or (ROOT / name).read_bytes() != payload
        ]
        if not SUMMARY_JSON_PATH.exists() or SUMMARY_JSON_PATH.read_bytes() != summary_json:
            changed.append(SUMMARY_JSON_PATH.relative_to(ROOT).as_posix())
        if not SUMMARY_MD_PATH.exists() or SUMMARY_MD_PATH.read_bytes() != summary_md:
            changed.append(SUMMARY_MD_PATH.relative_to(ROOT).as_posix())
        print("apply_spec_research: check-only; would_change=" + (", ".join(changed) if changed else "none"))
        return 0

    writes = []
    for name, payload in output_payloads.items():
        if _write_if_changed(ROOT / name, payload):
            writes.append(name)
    if _write_if_changed(SUMMARY_JSON_PATH, summary_json):
        writes.append(SUMMARY_JSON_PATH.relative_to(ROOT).as_posix())
    if _write_if_changed(SUMMARY_MD_PATH, summary_md):
        writes.append(SUMMARY_MD_PATH.relative_to(ROOT).as_posix())

    totals = application["totals"]
    print("apply_spec_research: ditulis=" + (", ".join(writes) if writes else "none (idempoten)"))
    print(
        "apply_spec_research: denominator=112 exact=%d skipped_non_exact=%d applied=%d conflicts=%d suggestions=%d"
        % (
            summary["research"]["exact"],
            totals["skipped_non_exact"],
            totals["applied_values"],
            totals["conflicts"],
            totals["suggestions_pending"],
        )
    )
    for name, state in summary["outputs"].items():
        print(f"apply_spec_research: sha256 {name}={state['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
