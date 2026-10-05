"""Evaluate independently labelled text; never generate ground truth from predictions."""
import hashlib
import time
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from modelling import sentiment_label,sentiment_score
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
