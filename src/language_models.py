"""Explicit opt-in FinBERT inference. No remote-code execution or silent fallback."""
import numpy as np
import pandas as pd
FINBERT_MODEL='ProsusAI/finbert'
FINBERT_REVISION='f210365adea9d5d19ff6a99f8658d1d94f58f584'


def load_finbert():
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError('FinBERT optional dependencies are missing; see requirements-finbert.txt.') from exc
    return pipeline('text-classification',model=FINBERT_MODEL,revision=FINBERT_REVISION,device=-1,trust_remote_code=False)


def finbert_predictions(texts,predictor=None):
    predictor=load_finbert() if predictor is None else predictor
    output=predictor(list(texts),top_k=None,truncation=True,max_length=512,batch_size=8)
    rows=[]
    if len(output)!=len(texts): raise ValueError('FinBERT output count does not match input.')
    for distribution in output:
        p={item['label'].lower():float(item['score']) for item in distribution}
        if set(p)!={'positive','negative','neutral'} or not np.isfinite(list(p.values())).all() or any(v<0 or v>1 for v in p.values()) or not np.isclose(sum(p.values()),1,atol=1e-4):
            raise ValueError('Unexpected FinBERT probability schema.')
        label=max(p,key=p.get)
        rows.append({'sentiment_label':label.title(),'sentiment_score':p['positive']-p['negative'],
                     'model_confidence':p[label],**{f'p_{k}':v for k,v in p.items()}})
    return pd.DataFrame(rows)
