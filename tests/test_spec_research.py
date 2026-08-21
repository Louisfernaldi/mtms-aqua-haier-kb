# -*- coding: utf-8 -*-
import copy
import json
import unittest
from pathlib import Path

from tools.apply_spec_research import (
    apply_bundle,
    apply_research_records,
    ensure_additional_categories,
)
from tools.gen_kompetitor import finalize_dynamic_specs
from tools.migrate_dynamic_specs import categories_list, iter_models, serialized_document
from tools.verify_dynamic_specs import find_user_overwrites
from tools.verify_spec_research import (
    CATEGORIES_PATH,
    COMPETITOR_PATH,
    PRODUCT_PATH,
    build_application_report,
    load_staging_documents,
    read_json,
    validate_research_contract,
)


ROOT = Path(__file__).resolve().parent.parent
URL = "https://example.com/exact-model"
STAMP = "2026-08-21T10:00:00+07:00"


def base_categories():
    document = read_json(CATEGORIES_PATH)
    document["spec_categories"] = copy.deepcopy(categories_list(document)[:12])
    document.pop("research_categories", None)
    return document


def staged(value, raw="Label resmi", source_kind="official_product_page"):
    return {
        "value": value,
        "raw_value": raw,
        "source_url": URL,
        "source_kind": source_kind,
        "verified_at": STAMP,
    }


def model(name, **changes):
    row = {
        "brand": "AQUA",
        "model": name,
        "spec_values": {},
        "research_suggestions": [],
    }
    row.update(changes)
    return row


def record(name, *, exact=True, specs=None, additional=None, notes=None):
    specs = specs or {}
    additional = additional or {}
    return {
        "model_id": f"AQUA::{name}",
        "brand": "AQUA",
        "model": name,
        "research_status": "partial" if exact else "unresolved",
        "exact_match": exact,
        "checked_urls": [URL],
        "specs": specs,
        "additional_specs": additional,
        "unresolved_core": [],
        "notes": notes or [],
    }


class SpecResearchMergeTests(unittest.TestCase):
    def test_exact_only_value_is_applied_with_raw_provenance(self):
        categories = base_categories()
        rows = [record("EXACT", specs={"width_mm": staged(600, "Width: 600 mm")})]
        result = apply_research_records([model("EXACT")], categories, rows)
        value = result[0]["spec_values"]["width_mm"]
        self.assertEqual(value["value"], 600)
        self.assertEqual(value["raw_value"], "Width: 600 mm")
        self.assertEqual(value["origin"], "research")
        self.assertIs(value["user_locked"], False)

    def test_non_exact_record_is_ignored_even_if_sabotaged_with_values(self):
        categories = base_categories()
        rows = [record("NEARBY", exact=False, specs={"width_mm": staged(777)})]
        result = apply_research_records([model("NEARBY")], categories, rows)
        self.assertNotIn("width_mm", result[0]["spec_values"])
        self.assertEqual(result[0]["research_suggestions"], [])

    def test_origin_user_and_user_locked_are_never_overwritten(self):
        protected_entries = (
            {"value": None, "source_url": None, "source_kind": None, "verified_at": None,
             "origin": "user", "user_locked": False},
            {"value": "Pilihan User", "source_url": None, "source_kind": None, "verified_at": None,
             "origin": "legacy", "user_locked": True},
        )
        for protected in protected_entries:
            with self.subTest(protected=protected):
                before = [model("LOCKED", spec_values={"cooling_system": protected})]
                result = apply_research_records(
                    before,
                    base_categories(),
                    [record("LOCKED", specs={"cooling_system": staged("No Frost")})],
                )
                self.assertEqual(
                    result[0]["spec_values"]["cooling_system"]["value"],
                    protected["value"],
                )
                self.assertEqual(find_user_overwrites(before, result), [])
                self.assertEqual(result[0]["research_suggestions"][0]["status"], "pending")

    def test_unprotected_conflict_becomes_pending_suggestion(self):
        existing = {
            "value": 500,
            "source_url": None,
            "source_kind": None,
            "verified_at": None,
            "origin": "legacy",
            "user_locked": False,
        }
        result = apply_research_records(
            [model("CONFLICT", spec_values={"width_mm": existing})],
            base_categories(),
            [record("CONFLICT", specs={"width_mm": staged(600, "Width: 600 mm")})],
        )
        self.assertEqual(result[0]["spec_values"]["width_mm"]["value"], 500)
        suggestion = result[0]["research_suggestions"][0]
        self.assertEqual(suggestion["value"], 600)
        self.assertEqual(suggestion["raw_value"], "Width: 600 mm")
        self.assertEqual(suggestion["status"], "pending")

    def test_notes_never_create_features_or_specs(self):
        result = apply_research_records(
            [model("NOTES")],
            base_categories(),
            [record("NOTES", specs={"door_count": staged(2)}, notes=["wifi=true; feature nearby"])],
        )
        self.assertEqual(set(result[0]["spec_values"]), {"door_count"})

    def test_unlabelled_capacity_stays_additional(self):
        categories = base_categories()
        rows = [record(
            "CAPACITY",
            additional={"capacity_unlabelled_l": staged(407, "Capacity 407 L")},
        )]
        ensure_additional_categories(categories, rows)
        result = apply_research_records([model("CAPACITY")], categories, rows)
        self.assertEqual(result[0]["spec_values"]["capacity_unlabelled_l"]["value"], 407)
        self.assertNotIn("gross_capacity_l", result[0]["spec_values"])
        self.assertNotIn("net_capacity_l", result[0]["spec_values"])
        self.assertNotIn("research_additional_values", result[0])

    def test_additional_category_is_global_deterministic_and_non_comparison(self):
        categories = base_categories()
        rows = [record("EXTRA", additional={"wifi_embedded": staged(True)})]
        ensure_additional_categories(categories, rows)
        ensure_additional_categories(categories, rows)
        matches = [item for item in categories["spec_categories"] if item["key"] == "wifi_embedded"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(categories_list(categories)), 13)
        self.assertEqual(
            [item["key"] for item in categories_list(categories)[:12]],
            [item["key"] for item in categories_list(base_categories())],
        )
        self.assertNotIn("research_categories", categories)
        self.assertEqual(matches[0]["group"], "Tambahan")
        self.assertIs(matches[0]["comparison"], False)
        self.assertIs(matches[0]["active"], True)
        self.assertEqual(matches[0]["order"], 130)

    def test_second_apply_is_semantic_and_byte_identical(self):
        rows = [record(
            "IDEMPOTENT",
            specs={"width_mm": staged(600)},
            additional={"wifi_embedded": staged(True)},
        )]
        categories_once = base_categories()
        ensure_additional_categories(categories_once, rows)
        once = apply_research_records([model("IDEMPOTENT")], categories_once, rows)
        categories_twice = copy.deepcopy(categories_once)
        ensure_additional_categories(categories_twice, rows)
        twice = apply_research_records(once, categories_twice, rows)
        self.assertEqual(serialized_document(once, indent=2), serialized_document(twice, indent=2))
        self.assertEqual(
            serialized_document(categories_once, indent=2),
            serialized_document(categories_twice, indent=2),
        )
        self.assertNotIn("research_additional_values", twice[0])
        self.assertNotIn("research_categories", categories_twice)

    def test_legacy_additional_user_value_is_folded_and_preserved(self):
        categories = base_categories()
        rows = [record("LEGACY", additional={"wifi_embedded": staged(False)})]
        ensure_additional_categories(categories, rows)
        user_value = {
            "value": True,
            "source_url": None,
            "source_kind": None,
            "verified_at": None,
            "origin": "user",
            "user_locked": True,
        }
        result = apply_research_records(
            [model("LEGACY", research_additional_values={"wifi_embedded": user_value})],
            categories,
            rows,
        )
        self.assertEqual(result[0]["spec_values"]["wifi_embedded"], user_value)
        self.assertEqual(result[0]["research_suggestions"][0]["key"], "wifi_embedded")
        self.assertEqual(result[0]["research_suggestions"][0]["status"], "pending")
        self.assertNotIn("research_additional_values", result[0])

    def test_full_bundle_keeps_ticket_03_baseline_and_single_contract(self):
        documents = load_staging_documents()
        competitor, products, categories = apply_bundle(
            read_json(COMPETITOR_PATH),
            read_json(PRODUCT_PATH),
            read_json(CATEGORIES_PATH),
            documents,
        )
        application, errors = build_application_report(documents, competitor, products)
        self.assertEqual(errors, [])
        self.assertEqual(application["totals"]["applied_values"], 885)
        self.assertEqual(application["totals"]["conflicts"], 36)
        self.assertEqual(application["totals"]["suggestions_pending"], 36)
        self.assertNotIn("research_categories", categories)
        for document in (competitor, products):
            for _brand, row in iter_models(document):
                self.assertNotIn("research_additional_values", row)
                self.assertNotIn("research_additional_suggestions", row)

    def test_generator_finalize_preserves_research_hash(self):
        documents = load_staging_documents()
        source = read_json(COMPETITOR_PATH)
        products = read_json(PRODUCT_PATH)
        categories = read_json(CATEGORIES_PATH)
        generated_base = copy.deepcopy(source)
        for brand in generated_base["brands"]:
            for row in brand["models"]:
                row.pop("model_id", None)
                row.pop("spec_values", None)
                row.pop("research_suggestions", None)
                row.pop("research_additional_values", None)
                row.pop("research_additional_suggestions", None)
        once, once_categories = finalize_dynamic_specs(
            copy.deepcopy(generated_base), products, copy.deepcopy(categories), documents
        )
        twice, twice_categories = finalize_dynamic_specs(
            copy.deepcopy(generated_base), products, copy.deepcopy(categories), documents
        )
        self.assertEqual(serialized_document(once), serialized_document(twice))
        self.assertEqual(serialized_document(once_categories, indent=2), serialized_document(twice_categories, indent=2))
        aqua = next(brand for brand in once["brands"] if brand["brand"] == "AQUA")
        researched = next(row for row in aqua["models"] if row["model"] == "AQR-350RBM")
        self.assertTrue(any(value.get("origin") == "research" for value in researched["spec_values"].values()))


class SpecResearchSabotageTests(unittest.TestCase):
    def setUp(self):
        self.documents = load_staging_documents()
        self.competitor = read_json(COMPETITOR_PATH)
        self.products = read_json(PRODUCT_PATH)

    def test_current_seven_file_contract_is_consistent(self):
        self.assertEqual(
            validate_research_contract(self.documents, self.competitor, self.products),
            [],
        )

    def test_sabotage_exact_gate_is_rejected(self):
        mutant = copy.deepcopy(self.documents)
        target = next(row for row in mutant["POLYTRON"]["records"] if not row["exact_match"])
        target["specs"]["width_mm"] = staged(999, "Nearby width 999 mm")
        target["unresolved_core"].remove("width_mm")
        errors = validate_research_contract(mutant, self.competitor, self.products)
        self.assertTrue(any("exact_match=false" in error for error in errors), errors)

    def test_sabotage_user_lock_is_detected(self):
        protected = {
            "value": "User",
            "source_url": None,
            "source_kind": None,
            "verified_at": None,
            "origin": "user",
            "user_locked": True,
        }
        before = [model("LOCK", spec_values={"cooling_system": protected})]
        after = copy.deepcopy(before)
        after[0]["spec_values"]["cooling_system"]["value"] = "Research"
        errors = find_user_overwrites(before, after)
        self.assertTrue(any("nilai user tertimpa" in error for error in errors), errors)

    def test_sabotage_unlabelled_capacity_promotion_is_rejected(self):
        mutant = copy.deepcopy(self.documents)
        target = mutant["MIDEA"]["records"][0]
        target["specs"]["gross_capacity_l"] = staged(407, "Unlabelled Capacity 407 L")
        target["unresolved_core"].remove("gross_capacity_l")
        errors = validate_research_contract(mutant, self.competitor, self.products)
        self.assertTrue(any("tidak boleh dipromosikan" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
