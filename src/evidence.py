"""Retrieve dated evidence and build an extractive brief with auditable references."""
import hashlib
import io
import json
import zipfile
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def retrieve_evidence(news,query='',as_of=None,limit=6):
    if limit<1: raise ValueError('Evidence limit must be positive.')
    cutoff=pd.Timestamp.now(tz='UTC') if as_of is None else pd.to_datetime(as_of,utc=True)
    eligible=news.loc[(~news.synthetic)&news.url.ne('')&(news.published_at<=cutoff)&(news.available_at<=cutoff)].copy()
    if eligible.empty: return eligible
    eligible=eligible.sort_values(['published_at','article_id'],ascending=[False,True])
    if query.strip():
        try:
            vectorizer=TfidfVectorizer(stop_words='english',ngram_range=(1,2))
            matrix=vectorizer.fit_transform(eligible.headline)
            eligible['relevance']=cosine_similarity(matrix,vectorizer.transform([query])).ravel()
        except ValueError:
            return eligible.iloc[:0]
        eligible=eligible.loc[eligible.relevance>0].sort_values(['relevance','published_at'],ascending=False)
    else: eligible['relevance']=1.
    return eligible.head(limit)


def evidence_brief(news,query='',as_of=None,limit=6):
    selected=retrieve_evidence(news,query,as_of,limit)
    claims=[{'text':r.headline,'article_ids':[r.article_id],'url':r.url,'source':r.source,
             'published_at':r.published_at.isoformat(),'available_at':r.available_at.isoformat()} for r in selected.itertuples()]
    return {'method':'Extractive source brief','query':query,'as_of':str(as_of or pd.Timestamp.now(tz='UTC')),
            'abstained':not bool(claims),'reason':'No relevant, verifiable sources available at the cutoff.' if not claims else '',
            'claims':claims,'note':'Quoted headlines are evidence of what the source reports, not independent verification or investment forecasts.'}


def audit_claims(claims,news,judgments=None):
    """Citation validity is NOT semantic entailment. Human judgments are separate."""
    sources=news.set_index('article_id'); rows=[]
    for i,claim in enumerate(claims):
        ids=claim.get('article_ids',[])
        valid=bool(ids) and all(a in sources.index and bool(sources.loc[a,'url']) and not bool(sources.loc[a,'synthetic']) for a in ids)
        exact=valid and any(claim['text'].strip()==sources.loc[a,'headline'].strip() for a in ids)
        label=None if judgments is None else judgments.get(str(i))
        if label not in {None,'supported','unsupported','unclear'}: raise ValueError('Unknown human support judgment.')
        rows.append({'claim':i,'valid_citations':valid,'exact_headline_extract':exact,'human_support':label})
    result=pd.DataFrame(rows,columns=['claim','valid_citations','exact_headline_extract','human_support'])
    return result


def export_bundle(news,brief,settings):
    out=io.BytesIO()
    metadata={**settings,'dataset_sha256':hashlib.sha256(news.to_csv(index=False).encode()).hexdigest()}
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('articles.csv',news.to_csv(index=False))
        z.writestr('brief.json',json.dumps(brief,indent=2))
        z.writestr('citation_audit.csv',audit_claims(brief['claims'],news).to_csv(index=False))
        z.writestr('settings.json',json.dumps(metadata,indent=2))
    return out.getvalue()
