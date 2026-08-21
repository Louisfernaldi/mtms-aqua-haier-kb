# -*- coding: utf-8 -*-
"""Migrasi deterministik skema spesifikasi dinamis MTMS.

``migrate_document(data, categories)`` tidak mengubah ``data`` masukan. Daftar
``categories`` sengaja diperbarui di tempat bila dokumen sudah mempunyai key
spesifikasi yang belum terdaftar: key tersebut menjadi kategori tambahan aktif,
non-utama, dan mendapat order stabil. Tidak ada nilai spesifikasi yang diriset
atau ditebak oleh migrator ini.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, MutableMapping, Tuple


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "site" / "data" / "kompetitor.json"
DEFAULT_CATEGORIES = ROOT / "site" / "data" / "spec-categories.json"

CORE_CATEGORY_KEYS = (
    "form_factor",
    "door_count",
    "freezer_position",
    "gross_capacity_l",
    "net_capacity_l",
    "width_mm",
    "height_mm",
    "depth_mm",
    "rated_power_w",
    "compressor_type",
    "cooling_system",
    "defrost_type",
)

SPEC_VALUE_FIELDS = (
    "value",
    "source_url",
    "source_kind",
    "verified_at",
    "origin",
    "user_locked",
)

# Pemetaan ini berasal dari categories[] lama di kompetitor.json/gen_kompetitor.py.
# capacity_l sengaja tidak dipetakan ke gross/nett: evidence taxonomy membuktikan
# maknanya tidak konsisten untuk model AQUA yang overlap dengan katalog.
LEGACY_FORM_FACTOR_BY_CAT = {
    "SB": "1 Pintu",
    "TM": "2 Pintu Top Mount",
    "BM": "2 Pintu Freezer Bawah",
    "SBS": "Side by Side",
    "MD": "Multi Pintu",
}

LEGACY_DIRECT_FIELDS = {
    "gross_capacity_l": "kapasitas_gross",
    "net_capacity_l": "kapasitas_nett",
    "rated_power_w": "daya_watt",
}


def categories_list(categories: Any) -> List[Dict[str, Any]]:
    """Ambil list kategori dari list langsung atau wrapper spec_categories[]."""

    if isinstance(categories, list):
        return categories
    if isinstance(categories, dict) and isinstance(categories.get("spec_categories"), list):
        return categories["spec_categories"]
    raise ValueError("categories harus list atau object dengan spec_categories[]")


def iter_models(document: Any) -> Iterator[Tuple[str, MutableMapping[str, Any]]]:
    """Yield (brand, model) tanpa mengubah struktur dokumen sumber."""

    if isinstance(document, list):
        for model in document:
            if not isinstance(model, dict):
                raise ValueError("record model harus object")
            yield str(model.get("brand") or ""), model
        return

    if not isinstance(document, dict):
        raise ValueError("dokumen harus object atau list")

    if isinstance(document.get("brands"), list):
        for brand_record in document["brands"]:
            if not isinstance(brand_record, dict) or not isinstance(brand_record.get("models"), list):
                raise ValueError("setiap brand harus object dengan models[]")
            brand = str(brand_record.get("brand") or "")
            for model in brand_record["models"]:
                if not isinstance(model, dict):
                    raise ValueError("record model harus object")
                yield brand, model
        return

    if isinstance(document.get("models"), list):
        brand = str(document.get("brand") or "")
        for model in document["models"]:
            if not isinstance(model, dict):
                raise ValueError("record model harus object")
            yield brand, model
        return

    raise ValueError("dokumen tidak mempunyai brands[] atau models[]")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def serialized_document(value: Any, indent: int = 1) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=indent) + "\n").encode("utf-8")


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _empty_value() -> Dict[str, Any]:
    return {
        "value": None,
        "source_url": None,
        "source_kind": None,
        "verified_at": None,
        "origin": "unknown",
        "user_locked": False,
    }


def has_meaningful_spec_state(entry: Dict[str, Any]) -> bool:
    """True bila entry sparse membawa nilai, provenance, lock, atau state ekstra."""

    if entry.get("value") is not None:
        return True
    if any(entry.get(field) is not None for field in ("source_url", "source_kind", "verified_at")):
        return True
    if entry.get("origin") == "user" or entry.get("user_locked") is True:
        return True
    return any(key not in SPEC_VALUE_FIELDS for key in entry)


def _normalize_value(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        locked = raw.get("user_locked") is True
        origin = raw.get("origin")
        if not isinstance(origin, str) or not origin:
            origin = "user" if locked else ("unknown" if _is_empty(raw.get("value")) else "legacy")
        protected = origin == "user" or locked
        value = raw.get("value")
        if not protected and _is_empty(value):
            value = None
        normalized = {
            "value": value,
            "source_url": raw.get("source_url"),
            "source_kind": raw.get("source_kind"),
            "verified_at": raw.get("verified_at"),
            "origin": origin,
            "user_locked": locked,
        }
        for key, value_extra in raw.items():
            if key not in normalized:
                normalized[key] = copy.deepcopy(value_extra)
        return normalized

    if _is_empty(raw):
        return _empty_value()
    return {
        "value": copy.deepcopy(raw),
        "source_url": None,
        "source_kind": None,
        "verified_at": None,
        "origin": "legacy",
        "user_locked": False,
    }


def _legacy_candidate(model: MutableMapping[str, Any], key: str) -> Dict[str, Any] | None:
    value = None
    found = False

    if key in model and not _is_empty(model.get(key)):
        value = copy.deepcopy(model[key])
        found = True
    elif key in LEGACY_DIRECT_FIELDS:
        old_key = LEGACY_DIRECT_FIELDS[key]
        if old_key in model and not _is_empty(model.get(old_key)):
            value = copy.deepcopy(model[old_key])
            found = True
    elif key == "form_factor":
        group = model.get("group")
        cat = model.get("cat")
        if isinstance(group, str) and group.strip():
            value = group
            found = True
        elif cat in LEGACY_FORM_FACTOR_BY_CAT:
            value = LEGACY_FORM_FACTOR_BY_CAT[cat]
            found = True

    if not found:
        return None

    source_url = model.get("source_url")
    if not isinstance(source_url, str) or not source_url.strip():
        source_url = None
    return {
        "value": value,
        "source_url": source_url,
        "source_kind": "legacy" if source_url else None,
        "verified_at": None,
        "origin": "legacy",
        "user_locked": False,
    }


def _suggestion(key: str, candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "key": key,
        "value": copy.deepcopy(candidate["value"]),
        "source_url": candidate.get("source_url"),
        "source_kind": candidate.get("source_kind"),
        "verified_at": candidate.get("verified_at"),
        "origin": candidate.get("origin"),
        "status": "pending",
    }


def _merge_candidate(
    key: str,
    existing: Dict[str, Any],
    candidate: Dict[str, Any] | None,
    suggestions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if candidate is None or candidate.get("value") is None:
        return existing

    protected = existing.get("origin") == "user" or existing.get("user_locked") is True
    if existing.get("value") is None and not protected:
        merged = copy.deepcopy(candidate)
        for extra_key, extra_value in existing.items():
            if extra_key not in SPEC_VALUE_FIELDS:
                merged[extra_key] = copy.deepcopy(extra_value)
        return merged

    if existing.get("value") == candidate.get("value"):
        return existing

    new_suggestion = _suggestion(key, candidate)
    fingerprints = {canonical_json(item) for item in suggestions}
    if canonical_json(new_suggestion) not in fingerprints:
        suggestions.append(new_suggestion)
    return existing


def _human_label(key: str) -> str:
    words = key.replace("-", " ").replace("_", " ").strip().split()
    return " ".join(word[:1].upper() + word[1:] for word in words) or key


def _next_additional_order(category_items: Iterable[Dict[str, Any]]) -> int:
    orders = [item.get("order") for item in category_items if isinstance(item.get("order"), int)]
    current = max(orders, default=0)
    return ((current // 10) + 1) * 10


def _collect_unknown_keys(document: Any, known: set[str]) -> List[str]:
    unknown: set[str] = set()
    for _, model in iter_models(document):
        raw_values = model.get("spec_values")
        if isinstance(raw_values, dict):
            for key, raw_value in raw_values.items():
                if (
                    isinstance(key, str)
                    and key
                    and key not in known
                    and has_meaningful_spec_state(_normalize_value(raw_value))
                ):
                    unknown.add(key)
        raw_suggestions = model.get("research_suggestions")
        if isinstance(raw_suggestions, list):
            for item in raw_suggestions:
                if isinstance(item, dict):
                    key = item.get("key")
                    if isinstance(key, str) and key and key not in known:
                        unknown.add(key)
    return sorted(unknown)


def _ensure_additional_categories(document: Any, categories: Any) -> List[Dict[str, Any]]:
    items = categories_list(categories)
    known = {item.get("key") for item in items if isinstance(item, dict)}
    for key in _collect_unknown_keys(document, known):
        items.append({
            "key": key,
            "label": _human_label(key),
            "group": "Tambahan",
            "unit": "-",
            "comparison": False,
            "order": _next_additional_order(items),
            "active": True,
        })
        known.add(key)
    return items


def migrate_document(data: Any, categories: Any) -> Any:
    """Kembalikan dokumen termigrasi yang deterministik dan idempoten.

    Field model lama dipertahankan. User value (``origin=user`` atau
    ``user_locked=true``) tidak pernah ditimpa; kandidat berbeda disimpan sebagai
    suggestion. Unknown spec key menambah kategori global non-utama pada object
    ``categories`` yang diberikan pemanggil.
    """

    result = copy.deepcopy(data)
    category_items = _ensure_additional_categories(result, categories)
    ordered_keys = [item["key"] for item in category_items]

    seen_model_ids: set[str] = set()
    for brand, model in iter_models(result):
        model_name = model.get("model")
        if not brand or not isinstance(model_name, str) or not model_name:
            raise ValueError("brand dan model wajib ada untuk membentuk model_id exact")
        model_id = f"{brand}::{model_name}"
        if model_id in seen_model_ids:
            raise ValueError(f"model_id duplikat: {model_id}")
        seen_model_ids.add(model_id)

        raw_values = model.get("spec_values")
        if raw_values is None:
            raw_values = {}
        if not isinstance(raw_values, dict):
            raise ValueError(f"{model_id}: spec_values harus object")

        raw_suggestions = model.get("research_suggestions")
        if raw_suggestions is None:
            suggestions: List[Dict[str, Any]] = []
        elif isinstance(raw_suggestions, list) and all(isinstance(item, dict) for item in raw_suggestions):
            suggestions = copy.deepcopy(raw_suggestions)
        else:
            raise ValueError(f"{model_id}: research_suggestions harus list of object")

        # Sparse representation: category yang absent dibaca sebagai unknown/null
        # oleh layer baca. Hanya state bermakna yang disimpan di JSON model.
        normalized_values: Dict[str, Dict[str, Any]] = {}
        for key in ordered_keys:
            existing = _normalize_value(raw_values.get(key)) if key in raw_values else _empty_value()
            candidate = _legacy_candidate(model, key)
            merged = _merge_candidate(key, existing, candidate, suggestions)
            if has_meaningful_spec_state(merged):
                normalized_values[key] = merged

        model["model_id"] = model_id
        model["spec_values"] = normalized_values
        model["research_suggestions"] = suggestions

    return result


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_if_changed(path: Path, payload: bytes) -> bool:
    if path.exists() and path.read_bytes() == payload:
        return False
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return True


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--categories", type=Path, default=DEFAULT_CATEGORIES)
    args = parser.parse_args(argv)

    categories_document = _read_json(args.categories)
    data = _read_json(args.data)
    migrated = migrate_document(data, categories_document)

    data_bytes = serialized_document(migrated, indent=1)
    category_bytes = serialized_document(categories_document, indent=2)
    data_changed = _write_if_changed(args.data, data_bytes)
    categories_changed = _write_if_changed(args.categories, category_bytes)
    model_count = sum(1 for _ in iter_models(migrated))
    digest = hashlib.sha256(data_bytes).hexdigest()
    state = "ditulis" if data_changed or categories_changed else "sudah sama (idempoten)"
    print(
        "migrate_dynamic_specs: %s; models=%d categories=%d sha256=%s"
        % (state, model_count, len(categories_list(categories_document)), digest)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
