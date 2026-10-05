"""Source-linked market research and explicit sentiment evaluation."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import json
import pandas as pd
import streamlit as st
from data_generation import generate_news
from ingestion import normalise_news,fetch_official_feeds,FEEDS
from modelling import score_news,generate_market_summary
from language_models import finbert_predictions
from evidence import evidence_brief,audit_claims,export_bundle
from evaluation import evaluate_sentiment

st.set_page_config(page_title='Market Intelligence Research',layout='wide')
st.title('Market Intelligence AI & Evidence')
st.caption('Trace market headlines to their sources and compare sentiment methods on labelled data.')
mode=st.sidebar.selectbox('News source',['Synthetic demonstration','Official feeds','Upload dated CSV'])
backend=st.sidebar.selectbox('Sentiment model',['Keyword baseline','FinBERT (optional)'])

@st.cache_data(ttl=900,show_spinner='Reading official feeds…')
def official(): return fetch_official_feeds()

if mode=='Synthetic demonstration':
    raw=generate_news(120)
    raw['source']='Synthetic demonstration';raw['synthetic']=True
    news=normalise_news(raw)
    diagnostics=[]
    st.warning('These headlines are generated examples. They are excluded from the sourced evidence brief.')
elif mode=='Official feeds':
    if st.button('Fetch official feeds'): st.session_state['official_news']=official()
    if 'official_news' not in st.session_state:
        st.info('Fetch the Federal Reserve and ECB feeds to begin. Downloads happen only when requested.')
        st.stop()
    news,diagnostics=st.session_state['official_news']
    st.dataframe(pd.DataFrame(diagnostics),hide_index=True)
    if news.empty: st.error('No feed could be loaded. Review source errors above.');st.stop()
else:
    upload=st.file_uploader('CSV with headline, published_at, url; optional source and recorded available_at',type=['csv'])
    if upload is None: st.stop()
    try: news=normalise_news(pd.read_csv(upload));diagnostics=[]
    except (ValueError,pd.errors.ParserError) as exc: st.error(str(exc));st.stop()

news=score_news(news)
if backend.startswith('FinBERT'):
    try:
        predictions=finbert_predictions(news.headline.tolist())
        for column in predictions: news[column]=predictions[column].to_numpy()
    except (ImportError,RuntimeError,OSError,ValueError) as exc:
        st.error(f'FinBERT could not run: {exc}')
        st.stop()
cols=st.columns(3)
cols[0].metric('Distinct headlines',len(news))
cols[1].metric('Publisher/source labels',news.source.nunique())
cols[2].metric('Negative sentiment',int(news.sentiment_label.eq('Negative').sum()))
brief_tab,explorer,research=st.tabs(['Evidence brief','News explorer','Research evaluation'])
with brief_tab:
    query=st.text_input('Research question or search terms','interest rates')
    cutoff=st.text_input('Evidence cutoff (UTC ISO timestamp)',pd.Timestamp.now(tz='UTC').floor('s').isoformat())
    try: brief=evidence_brief(news,query,cutoff)
    except (ValueError,TypeError) as exc: st.error(f'Invalid cutoff: {exc}');st.stop()
    if brief['abstained']: st.info(brief['reason'])
    for claim in brief['claims']:
        st.write(claim['text'])
        st.link_button(f"Source: {claim['source']} · {claim['published_at'][:10]}",claim['url'])
    st.caption('Extractive brief: headlines retain source wording. Availability means first observation by this ingestion run unless an archive supplies its recorded timestamp. Links do not independently verify a claim.')
    st.download_button('Download evidence and research settings',export_bundle(news,brief,{'sentiment_model':backend,'feed_diagnostics':diagnostics}),
                       'market_research.zip','application/zip')
with explorer:
    st.dataframe(news[['published_at','available_at','source','headline','url','sentiment_label','sentiment_score','risk_flags']],hide_index=True)
    st.caption('Sentiment describes language, not a prediction of returns. Historical publication dates alone do not establish historical availability to this system.')
    st.write('Template baseline for comparison:')
    st.info(generate_market_summary(news))
with research:
    st.write('Compare keyword and FinBERT predictions against independently assigned sentiment labels.')
    evaluation_upload=st.file_uploader('Evaluation CSV: headline,label (Positive, Neutral, Negative)',type=['csv'],key='eval')
    evaluation_data=pd.read_csv(evaluation_upload) if evaluation_upload else pd.read_csv(Path(__file__).parent/'data/evaluation/diagnostic_cases.csv')
    if evaluation_upload is None: st.caption('Default: small author-labelled synthetic diagnostics. These are functional checks, not an external benchmark.')
    if st.button('Evaluate selected sentiment model'):
        try:
            report=evaluate_sentiment(evaluation_data,'finbert' if backend.startswith('FinBERT') else 'lexicon')
            st.json(report)
            st.download_button('Download evaluation report',json.dumps(report,indent=2),'sentiment_evaluation.json','application/json')
        except (ValueError,RuntimeError,OSError) as exc: st.error(str(exc))
    st.write('Source audit for this brief')
    st.dataframe(audit_claims(brief['claims'],news),hide_index=True)
    st.caption('Citation validity and exact extraction are mechanical checks. Comparing factual support across generated briefs requires separate supported/unsupported/unclear human judgments, available through the research API.')
