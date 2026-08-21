# -*- coding: utf-8 -*-
import copy
import json
import unittest
from pathlib import Path

from tools.migrate_dynamic_specs import categories_list, migrate_document, serialized_document
from tools.verify_dynamic_specs import (
    find_lost_model_fields,
    find_user_overwrites,
    validate_categories,
    validate_document,
)


ROOT = Path(__file__).resolve().parent.parent


def load_categories():
    return json.loads((ROOT / "site" / "data" / "spec-categories.json").read_text(encoding="utf-8"))


def legacy_model(**changes):
    model = {
        "model": "MODEL-1",
        "subcat": None,
        "cat": None,
        "door": None,
        "capacity_l": None,
        "price_idr": None,
        "price_source": None,
        "fitur": [],
        "image": None,
        "photo_url": None,
        "source_url": "https://example.com/MODEL-1",
    }
    model.update(changes)
    return model


def document(model=None):
    return {
        "brands": [
            {
                "brand": "AQUA",
                "model_count": 1,
                "models": [model or legacy_model()],
            }
        ]
    }


class DynamicSpecsMigrationTests(unittest.TestCase):
    def test_empty_model_uses_sparse_spec_values(self):
        categories = load_categories()
        migrated = migrate_document(document(), categories)
        values = migrated["brands"][0]["models"][0]["spec_values"]
        self.assertEqual(values, {})

    def test_empty_unknown_key_is_dropped_without_adding_category(self):
        categories = load_categories()
        empty_unknown = {
            "value": None,
            "source_url": None,
            "source_kind": None,
            "verified_at": None,
            "origin": "unknown",
            "user_locked": False,
        }
        migrated = migrate_document(
            document(legacy_model(spec_values={"empty_unknown": empty_unknown})),
            categories,
        )
        self.assertEqual(migrated["brands"][0]["models"][0]["spec_values"], {})
        self.assertEqual(len(categories_list(categories)), 12)

    def test_unknown_key_becomes_deterministic_non_comparison_category(self):
        categories = load_categories()
        unknown = {
            "value": True,
            "source_url": "https://example.com/MODEL-1",
            "source_kind": "brand_official",
            "verified_at": "2026-08-21T10:00:00+07:00",
            "origin": "research",
            "user_locked": False,
        }
        migrated = migrate_document(document(legacy_model(spec_values={"ice_maker": unknown})), categories)
        added = categories_list(categories)[-1]
        self.assertEqual(added["key"], "ice_maker")
        self.assertEqual(added["order"], 130)
        self.assertIs(added["comparison"], False)
        self.assertIs(added["active"], True)
        self.assertEqual(
            migrated["brands"][0]["models"][0]["spec_values"]["ice_maker"]["value"],
            True,
        )

    def test_user_value_is_not_overwritten_and_conflict_becomes_suggestion(self):
        categories = load_categories()
        user_value = {
            "value": "Pilihan User",
            "source_url": None,
            "source_kind": None,
            "verified_at": None,
            "origin": "user",
            "user_locked": True,
        }
        before = document(legacy_model(cat="TM", spec_values={"form_factor": user_value}))
        after = migrate_document(before, categories)
        model = after["brands"][0]["models"][0]
        self.assertEqual(model["spec_values"]["form_factor"]["value"], "Pilihan User")
        self.assertEqual(find_user_overwrites(before, after), [])
        self.assertEqual(len(model["research_suggestions"]), 1)
        self.assertEqual(model["research_suggestions"][0]["key"], "form_factor")
        self.assertEqual(model["research_suggestions"][0]["value"], "2 Pintu Top Mount")

    def test_protected_null_value_is_not_filled_and_candidate_becomes_suggestion(self):
        protected_values = {
            "origin_user": {
                "value": None,
                "source_url": None,
                "source_kind": None,
                "verified_at": None,
                "origin": "user",
                "user_locked": False,
            },
            "user_locked": {
                "value": None,
                "source_url": None,
                "source_kind": None,
                "verified_at": None,
                "origin": "legacy",
                "user_locked": True,
            },
        }

        for case_name, protected_value in protected_values.items():
            with self.subTest(case=case_name):
                categories = load_categories()
                before = document(
                    legacy_model(
                        cat="TM",
                        spec_values={"form_factor": protected_value},
                    )
                )
                after = migrate_document(before, categories)
                model = after["brands"][0]["models"][0]
                value = model["spec_values"]["form_factor"]

                self.assertIsNone(value["value"])
                self.assertEqual(value["origin"], protected_value["origin"])
                self.assertIs(value["user_locked"], protected_value["user_locked"])
                self.assertEqual(find_user_overwrites(before, after), [])
                self.assertEqual(len(model["research_suggestions"]), 1)
                self.assertEqual(model["research_suggestions"][0]["key"], "form_factor")
                self.assertEqual(
                    model["research_suggestions"][0]["value"],
                    "2 Pintu Top Mount",
                )

    def test_duplicate_category_is_rejected(self):
        categories = load_categories()
        duplicate = copy.deepcopy(categories_list(categories)[0])
        duplicate["order"] = 130
        categories_list(categories).append(duplicate)
        errors = validate_categories(categories)
        self.assertTrue(any("key kategori duplikat" in error for error in errors), errors)

    def test_invalid_research_source_is_rejected(self):
        categories = load_categories()
        migrated = migrate_document(document(), categories)
        migrated["brands"][0]["models"][0]["spec_values"]["width_mm"] = {
            "value": 600,
            "source_url": "javascript:alert(1)",
            "source_kind": "brand_official",
            "verified_at": "bukan-timestamp",
            "origin": "research",
            "user_locked": False,
        }
        errors = validate_document(migrated, categories)
        self.assertTrue(any("source_url invalid" in error for error in errors), errors)
        self.assertTrue(any("verified_at invalid" in error for error in errors), errors)

    def test_materialized_empty_state_is_rejected(self):
        categories = load_categories()
        migrated = migrate_document(document(), categories)
        migrated["brands"][0]["models"][0]["spec_values"]["width_mm"] = {
            "value": None,
            "source_url": None,
            "source_kind": None,
            "verified_at": None,
            "origin": "unknown",
            "user_locked": False,
        }
        errors = validate_document(migrated, categories)
        self.assertTrue(any("state unknown kosong wajib dihilangkan" in error for error in errors), errors)

    def test_orphan_category_is_rejected(self):
        categories = load_categories()
        migrated = migrate_document(document(), categories)
        migrated["brands"][0]["models"][0]["spec_values"]["orphan_key"] = {
            "value": "bermakna",
            "source_url": None,
            "source_kind": None,
            "verified_at": None,
            "origin": "legacy",
            "user_locked": False,
        }
        errors = validate_document(migrated, categories)
        self.assertTrue(any("kategori yatim" in error for error in errors), errors)

    def test_legacy_fields_are_not_lost(self):
        categories = load_categories()
        before = document(legacy_model(cat="SBS", capacity_l=500, custom_legacy={"keep": True}))
        after = migrate_document(before, categories)
        self.assertEqual(find_lost_model_fields(before, after), [])
        before_model = before["brands"][0]["models"][0]
        after_model = after["brands"][0]["models"][0]
        for key, value in before_model.items():
            self.assertEqual(after_model[key], value)

    def test_second_migration_is_semantic_and_byte_identical(self):
        categories_once = load_categories()
        source = document(legacy_model(cat="BM"))
        once = migrate_document(source, categories_once)
        categories_twice = copy.deepcopy(categories_once)
        twice = migrate_document(once, categories_twice)
        self.assertEqual(once, twice)
        self.assertEqual(serialized_document(once), serialized_document(twice))
        self.assertEqual(
            serialized_document(categories_once, indent=2),
            serialized_document(categories_twice, indent=2),
        )


if __name__ == "__main__":
    unittest.main()
