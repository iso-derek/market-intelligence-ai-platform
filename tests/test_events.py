"""D3.2 event taxonomy, linkage, and evaluation tests."""
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from entities import load_entity_registry, resolve_news_entities  # noqa: E402
from events import (  # noqa: E402
    EVENT_RULE_VERSION,
    classify_event,
    classify_news_events,
    evaluate_event_classifier,
    link_events_to_entities,
)


class EventTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_entity_registry(ROOT / "data" / "fixtures" / "entity_registry.csv")

    def test_each_taxonomy_class_has_a_deterministic_example(self):
        examples = {
            "Earnings": "Company reports revenue",
            "Guidance": "Company raises outlook",
            "Regulation": "Company faces antitrust probe",
            "M&A": "Company agrees to merger",
            "Financing": "Company prices a bond",
            "Operations": "Company begins layoffs",
            "Macroeconomic": "Central bank discusses inflation",
        }
        for expected, headline in examples.items():
            result = classify_event(headline)
            self.assertEqual(result["event_status"], "classified")
            self.assertEqual(result["event_type"], expected)
            self.assertEqual(result["event_rule_version"], EVENT_RULE_VERSION)

    def test_tied_categories_are_ambiguous(self):
        result = classify_event("Company raises outlook after record revenue")
        self.assertEqual(result["event_status"], "ambiguous")
        self.assertEqual(result["event_candidates"], "Earnings|Guidance")

    def test_no_match_is_unknown(self):
        result = classify_event("Company hosts annual meeting")
        self.assertEqual(result["event_status"], "unknown")
        self.assertEqual(result["event_type"], "")

    def test_word_boundaries_prevent_partial_event_matches(self):
        self.assertEqual(classify_event("Profitable software update")["event_status"], "unknown")

    def test_events_link_to_multiple_resolved_entities(self):
        news = pd.DataFrame({"article_id": ["a"], "headline": ["Apple and Microsoft announce a partnership"]})
        events = classify_news_events(news)
        resolutions = resolve_news_entities(news, self.registry)
        linked = link_events_to_entities(events, resolutions)
        self.assertEqual(set(linked.ticker), {"AAPL", "MSFT"})
        self.assertEqual(set(linked.entity_link_status), {"linked"})

    def test_ambiguous_entity_is_not_forced_into_link(self):
        news = pd.DataFrame({"article_id": ["a"], "headline": ["Alpha announces a merger"]})
        linked = link_events_to_entities(classify_news_events(news), resolve_news_entities(news, self.registry))
        self.assertEqual(linked.entity_link_status.item(), "ambiguous")
        self.assertEqual(linked.entity_id.item(), "")
        self.assertEqual(linked.entity_candidates.item(), "ent_alp|ent_axc")

    def test_labelled_fixture_evaluation_exports_metrics_and_hash(self):
        cases = pd.read_csv(ROOT / "data" / "evaluation" / "event_taxonomy_cases.csv")
        report = evaluate_event_classifier(cases)
        self.assertEqual(report["examples"], 24)
        self.assertEqual(len(report["dataset_sha256"]), 64)
        self.assertEqual(report["rule_version"], EVENT_RULE_VERSION)
        self.assertGreaterEqual(report["accuracy"], 0.9)
        self.assertIn("Macroeconomic", report["per_class"])
        self.assertEqual(len(report["confusion_matrix"]), len(report["labels"]))

    def test_evaluation_requires_independent_labels(self):
        with self.assertRaisesRegex(ValueError, "label"):
            evaluate_event_classifier(pd.DataFrame({"headline": ["Company reports revenue"]}))


if __name__ == "__main__":
    unittest.main()
