"""D3.3 frozen holdout, uncertainty, and overlap tests."""
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from evaluation import evaluate_sentiment_with_uncertainty  # noqa: E402


class RobustSentimentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=pd.read_csv(ROOT/'data/evaluation/sentiment_holdout.csv')

    def test_holdout_is_balanced_distinct_and_frozen(self):
        self.assertEqual(len(self.cases),30)
        self.assertFalse(self.cases.headline.str.casefold().duplicated().any())
        self.assertEqual(self.cases.label.value_counts().to_dict(),{'Positive':10,'Negative':10,'Neutral':10})
        self.assertEqual(set(self.cases.split),{'holdout'})

    def test_report_exports_per_class_metrics_and_corpus_identity(self):
        report=evaluate_sentiment_with_uncertainty(self.cases,resamples=200,seed=7)
        self.assertEqual(set(report['per_class']),{'Negative','Neutral','Positive'})
        self.assertEqual(len(report['data_sha256']),64)
        self.assertEqual(report['model_revision'],'local lexicon v2')
        self.assertEqual(report['corpus']['split'],'frozen holdout')
        self.assertEqual(report['corpus']['review_status'],['author-reviewed'])

    def test_bootstrap_intervals_are_bounded_and_reproducible(self):
        first=evaluate_sentiment_with_uncertainty(self.cases,resamples=200,seed=11)['uncertainty']
        second=evaluate_sentiment_with_uncertainty(self.cases,resamples=200,seed=11)['uncertainty']
        self.assertEqual(first,second)
        for metric in ['accuracy','macro_f1']:
            low,high=first[metric]
            self.assertTrue(0<=low<=high<=1)

    def test_overlap_review_is_case_level_and_not_hidden(self):
        overlap=evaluate_sentiment_with_uncertainty(self.cases,resamples=100)['overlap_review']
        self.assertEqual(len(overlap['matched_terms_by_case']),30)
        self.assertGreater(overlap['headlines_with_rule_terms'],0)
        self.assertLess(overlap['headlines_with_rule_terms'],30)
        self.assertIn('expected',overlap['interpretation'])

    def test_scores_are_not_perfect_on_the_frozen_holdout(self):
        report=evaluate_sentiment_with_uncertainty(self.cases,resamples=100)
        self.assertGreater(report['accuracy'],0.5)
        self.assertLess(report['accuracy'],1.0)
        self.assertGreater(report['macro_f1'],0.5)

    def test_optional_backend_revision_remains_explicit(self):
        def predictor(_texts,**_kwargs):
            distribution=[
                {'label':'positive','score':.8},
                {'label':'negative','score':.1},
                {'label':'neutral','score':.1},
            ]
            return [distribution for _ in range(len(_texts))]
        report=evaluate_sentiment_with_uncertainty(self.cases,'finbert',predictor,resamples=100)
        self.assertNotEqual(report['model_revision'],'local lexicon v2')
        self.assertEqual(report['backend'],'finbert')


if __name__=='__main__': unittest.main()
