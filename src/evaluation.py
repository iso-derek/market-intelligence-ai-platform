"""Evaluate independently labelled text; never generate ground truth from predictions."""
import hashlib
import re
import time
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix,precision_recall_fscore_support
from modelling import sentiment_label,sentiment_score,POSITIVE_WORDS,NEGATIVE_WORDS
from language_models import finbert_predictions,FINBERT_MODEL,FINBERT_REVISION
LABELS=['Negative','Neutral','Positive']


def evaluate_sentiment(frame,backend='lexicon',predictor=None):
    if not {'headline','label'}.issubset(frame): raise ValueError('Evaluation CSV needs headline and human label.')
    if frame.headline.isna().any() or frame.headline.str.strip().eq('').any() or frame.headline.str.casefold().duplicated().any():
        raise ValueError('Use distinct, non-empty evaluation headlines.')
    if len(frame)<3 or not set(frame.label).issubset(LABELS): raise ValueError('Use at least three valid human-labelled examples.')
    start=time.perf_counter()
    if backend=='finbert': predictions=finbert_predictions(frame.headline.tolist(),predictor).sentiment_label.tolist()
    elif backend=='lexicon': predictions=[sentiment_label(sentiment_score(text)) for text in frame.headline]
    else: raise ValueError('Unknown sentiment backend.')
    return {'backend':backend,'model_revision':FINBERT_REVISION if backend=='finbert' else 'local lexicon v2',
            'examples':len(frame),'accuracy':float(accuracy_score(frame.label,predictions)),
            'macro_f1':float(f1_score(frame.label,predictions,labels=LABELS,average='macro',zero_division=0)),
            'confusion_matrix':confusion_matrix(frame.label,predictions,labels=LABELS).tolist(),'label_order':LABELS,
            'seconds':time.perf_counter()-start,'predictions':predictions,
            'data_sha256':hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest(),
            'limit':'Score applies only to supplied labels. Check overlap with pretrained model training data before claiming unseen-data performance.'}


def _bootstrap_intervals(labels,predictions,resamples=500,seed=42,confidence=.95):
    if resamples<100: raise ValueError('Use at least 100 bootstrap resamples.')
    if not 0<confidence<1: raise ValueError('Confidence must be between 0 and 1.')
    labels=np.asarray(labels);predictions=np.asarray(predictions)
    rng=np.random.default_rng(seed);n=len(labels)
    accuracy=[];macro_f1=[]
    for _ in range(resamples):
        indices=rng.integers(0,n,size=n)
        accuracy.append(accuracy_score(labels[indices],predictions[indices]))
        macro_f1.append(f1_score(labels[indices],predictions[indices],labels=LABELS,average='macro',zero_division=0))
    tail=(1-confidence)/2
    return {
        'method':'nonparametric bootstrap over labelled examples',
        'confidence':confidence,'resamples':resamples,'seed':seed,
        'accuracy':[float(np.quantile(accuracy,tail)),float(np.quantile(accuracy,1-tail))],
        'macro_f1':[float(np.quantile(macro_f1,tail)),float(np.quantile(macro_f1,1-tail))],
    }


def _overlap_review(frame):
    rule_terms=POSITIVE_WORDS|NEGATIVE_WORDS
    rows=[]
    for headline in frame.headline:
        tokens=set(re.findall(r'[a-z]+',str(headline).casefold()))
        rows.append(sorted(tokens&rule_terms))
    covered=sum(bool(terms) for terms in rows)
    return {
        'rule_vocabulary':sorted(rule_terms),
        'headlines_with_rule_terms':covered,
        'headline_overlap_share':covered/len(rows),
        'matched_terms_by_case':['|'.join(terms) for terms in rows],
        'interpretation':'Rule-term overlap is expected for a transparent lexicon baseline and must be reviewed before calling the corpus unseen.',
    }


def evaluate_sentiment_with_uncertainty(frame,backend='lexicon',predictor=None,resamples=500,seed=42):
    """Add per-class metrics, bootstrap intervals, and overlap evidence."""
    report=evaluate_sentiment(frame,backend,predictor)
    labels=frame.label.tolist();predictions=report['predictions']
    precision,recall,f1,support=precision_recall_fscore_support(
        labels,predictions,labels=LABELS,zero_division=0)
    report['per_class']={
        label:{'precision':float(precision[i]),'recall':float(recall[i]),'f1':float(f1[i]),'support':int(support[i])}
        for i,label in enumerate(LABELS)}
    report['uncertainty']=_bootstrap_intervals(labels,predictions,resamples,seed)
    report['overlap_review']=_overlap_review(frame)
    report['corpus']={
        'split':'frozen holdout' if 'split' in frame and frame['split'].eq('holdout').all() else 'user supplied',
        'review_status':sorted(frame.review_status.dropna().unique().tolist()) if 'review_status' in frame else [],
        'source_groups':sorted(frame.source_group.dropna().unique().tolist()) if 'source_group' in frame else [],
    }
    return report
