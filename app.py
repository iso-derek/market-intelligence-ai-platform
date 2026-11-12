"""Source-linked market research and explicit sentiment evaluation."""
from pathlib import Path
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import json
import pandas as pd
import streamlit as st
from data_generation import generate_news
from ingestion import FEEDS,normalise_news,fetch_registered_feeds
from modelling import score_news,generate_market_summary
from language_models import finbert_predictions
from evidence import evidence_brief,audit_claims,export_bundle
from evaluation import evaluate_sentiment,evaluate_sentiment_with_uncertainty
from persistence import EvidenceStore
from market_dashboard import render_market_dashboard
from entities import load_entity_registry,resolve_news_entities,resolution_summary
from events import classify_news_events,link_events_to_entities,evaluate_event_classifier
from filings_dashboard import render_filings_dashboard
from workflow_dashboard import render_workflow_dashboard
from graph_dashboard import render_graph_dashboard
from watchlist_dashboard import render_watchlist_dashboard

st.set_page_config(page_title='Market Intelligence AI Platform',page_icon='📈',layout='wide',initial_sidebar_state='expanded')
st.title('Market Intelligence AI Platform')
st.caption('Point-in-time finance analytics and source-grounded market research in one auditable workspace.')
workspace=st.sidebar.radio(
    'Workspace',
    ['News evidence','Analyst watchlist','Market, macro & fundamentals','Filings corpus','Research workflow','Evidence graph & operations'],
    key='workspace',
    bind='query-params',
)
if workspace=='Analyst watchlist':
    render_watchlist_dashboard()
    st.stop()
if workspace=='Market, macro & fundamentals':
    render_market_dashboard()
    st.stop()
if workspace=='Filings corpus':
    render_filings_dashboard()
    st.stop()
if workspace=='Research workflow':
    render_workflow_dashboard()
    st.stop()
if workspace=='Evidence graph & operations':
    render_graph_dashboard()
    st.stop()
st.sidebar.header('Research controls')
mode=st.sidebar.selectbox('News source',['Synthetic demonstration','Official feeds','Upload dated CSV'])
backend=st.sidebar.selectbox('Sentiment model',['Keyword baseline','FinBERT (optional)'])
st.sidebar.info('News scope: headline evidence and sentiment research. Filings QA and typed workflows are available in their dedicated workspaces.')

@st.cache_resource
def open_evidence_store(path): return EvidenceStore(path)

@st.cache_data
def open_entity_registry(path): return load_entity_registry(path)

database_path=Path(os.environ.get('MARKET_INTELLIGENCE_DB',Path(__file__).parent/'data/runtime/evidence.db'))
store=open_evidence_store(str(database_path))
store.ensure_sources(FEEDS)

if mode=='Synthetic demonstration':
    raw=generate_news(120)
    raw['source']='Synthetic demonstration';raw['synthetic']=True
    news=normalise_news(raw)
    diagnostics=[]
    st.warning('These headlines are generated examples. They are excluded from the sourced evidence brief.')
elif mode=='Official feeds':
    registry=store.list_sources()
    st.subheader('Persistent source registry')
    st.caption(f'SQLite schema v{store.schema_version()} · persistent local evidence store')
    with st.expander('Manage registered sources'):
        editable=st.data_editor(
            registry[['source_id','name','feed_url','enabled','last_status','last_checked_at','last_error']],
            key='source_registry_editor',hide_index=True,
            disabled=['source_id','name','feed_url','last_status','last_checked_at','last_error'],
            column_config={'feed_url':st.column_config.LinkColumn('Feed URL')},
            alt='Editable official source registry',
        )
        if st.button('Save source settings',icon=':material/save:',key='save_source_settings'):
            for row in editable.itertuples(index=False): store.set_enabled(row.source_id,bool(row.enabled))
            st.success('Source settings saved.')
            st.rerun()
        with st.form('register_source_form',border=True):
            source_name=st.text_input('Source name')
            source_url=st.text_input('Public HTTPS RSS or Atom URL')
            add_source=st.form_submit_button('Register source',icon=':material/add_link:')
        if add_source:
            try:
                store.register_source(source_name,source_url)
                st.success('Source registered. Review and fetch it from the source list.')
                st.rerun()
            except (ValueError,TypeError) as exc: st.error(str(exc))
        snapshots=store.snapshots()
        if not snapshots.empty:
            selected_snapshot=st.selectbox(
                'Replayable snapshot',snapshots.snapshot_hash.tolist(),
                format_func=lambda value:f'{value[:12]}…',key='snapshot_export')
            st.download_button(
                'Download immutable snapshot',store.export_snapshot(selected_snapshot),
                f'{selected_snapshot}.zip','application/zip',icon=':material/download:')

    enabled=store.list_sources(enabled_only=True)
    if enabled.empty:
        st.warning('No sources are enabled. Enable at least one registry entry to fetch evidence.')
        st.stop()
    names=enabled.name.tolist()
    selected_names=st.multiselect('Sources to fetch',names,default=names,key='selected_sources')
    selected_ids=enabled.loc[enabled.name.isin(selected_names),'source_id'].tolist()
    if st.button('Fetch selected sources',icon=':material/sync:',disabled=not selected_ids):
        with st.spinner('Fetching, hashing, and storing source snapshots…'):
            news,diagnostics=fetch_registered_feeds(store,selected_ids)
        st.session_state['official_diagnostics']=diagnostics
        st.rerun()
    else:
        news=store.eligible_evidence()
        diagnostics=st.session_state.get('official_diagnostics',[])
    status=store.list_sources()[['name','enabled','last_status','last_checked_at','last_error']]
    st.dataframe(status,hide_index=True,alt='Registered source health and latest fetch status')
    if diagnostics:
        st.dataframe(pd.DataFrame(diagnostics),hide_index=True,alt='Latest official source fetch diagnostics')
    if news.empty:
        st.info('No persisted official evidence is available yet. Fetch an enabled source to begin.')
        st.stop()
else:
    upload=st.file_uploader('CSV with headline, published_at, url; optional source and recorded available_at',type=['csv'])
    if upload is None: st.stop()
    try: news=normalise_news(pd.read_csv(upload));diagnostics=[]
    except (ValueError,pd.errors.ParserError) as exc: st.error(str(exc));st.stop()

news=score_news(news)
entity_registry=open_entity_registry(str(Path(__file__).parent/'data/fixtures/entity_registry.csv'))
entity_resolutions=resolve_news_entities(news,entity_registry)
event_rows=classify_news_events(news)
event_links=link_events_to_entities(event_rows,entity_resolutions)
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
    st.subheader('Source-grounded headline evidence')
    query=st.text_input('Research question or search terms','interest rates')
    cutoff=st.text_input('Evidence cutoff (UTC ISO timestamp)',pd.Timestamp.now(tz='UTC').floor('s').isoformat())
    try: brief=evidence_brief(news,query,cutoff)
    except (ValueError,TypeError) as exc: st.error(f'Invalid cutoff: {exc}');st.stop()
    if brief['abstained']: st.info(brief['reason'])
    for claim in brief['claims']:
        st.write(claim['text'])
        st.link_button(f"Source: {claim['source']} · {claim['published_at'][:10]}",claim['url'])
    st.caption('Extractive brief: headlines retain source wording. Availability means first observation by this ingestion run unless an archive supplies its recorded timestamp. Links do not independently verify a claim.')
    with st.expander('How to interpret this brief'):
        st.write('A returned item passed the source, timestamp and lexical-relevance filters. It is evidence of what that source reported, not a verified fact, causal explanation or investment forecast.')
    st.download_button('Download evidence and research settings',export_bundle(news,brief,{'sentiment_model':backend,'feed_diagnostics':diagnostics}),
                       'market_research.zip','application/zip')
with explorer:
    st.subheader('Normalised news records')
    st.dataframe(news[['published_at','available_at','source','headline','url','sentiment_label','sentiment_score','risk_flags']],hide_index=True,
                 alt='Normalised market-news evidence with provenance and sentiment')
    st.caption('Sentiment describes language, not a prediction of returns. Historical publication dates alone do not establish historical availability to this system.')
    st.subheader('Entity and ticker resolution')
    entity_counts=resolution_summary(entity_resolutions)
    entity_columns=st.columns(3)
    entity_columns[0].metric('Resolved records',entity_counts['resolved'],border=True)
    entity_columns[1].metric('Ambiguous records',entity_counts['ambiguous'],border=True)
    entity_columns[2].metric('Unknown records',entity_counts['unknown'],border=True)
    st.dataframe(
        entity_resolutions[['headline','mention','canonical_name','ticker','sector','resolution_status','candidate_ids','resolution_version']],
        hide_index=True,alt='Conservative entity and ticker resolution outcomes for the current news records')
    st.caption('Exact registry aliases only. Ambiguous and unknown mentions remain unresolved; a company mention does not imply an effect on returns.')
    st.subheader('Event taxonomy and company linkage')
    event_counts=event_rows.event_status.value_counts()
    event_columns=st.columns(3)
    event_columns[0].metric('Classified events',int(event_counts.get('classified',0)),border=True)
    event_columns[1].metric('Ambiguous events',int(event_counts.get('ambiguous',0)),border=True)
    event_columns[2].metric('Unknown events',int(event_counts.get('unknown',0)),border=True)
    st.dataframe(
        event_links[['headline','event_type','event_status','event_candidates','matched_terms','canonical_name','ticker','sector','entity_link_status','event_rule_version']],
        hide_index=True,alt='Event taxonomy outcomes linked conservatively to resolved companies and sectors')
    st.caption('Taxonomy describes headline language only. Co-mention does not prove the event, materiality, causality, or an effect on returns.')
    st.write('Rule-based summary baseline:')
    st.info(generate_market_summary(news))
with research:
    st.subheader('Sentiment evaluation')
    st.write('Compare keyword and FinBERT predictions against independently assigned sentiment labels.')
    evaluation_upload=st.file_uploader('Evaluation CSV: headline,label (Positive, Neutral, Negative)',type=['csv'],key='eval')
    try:
        evaluation_data=pd.read_csv(evaluation_upload) if evaluation_upload else pd.read_csv(Path(__file__).parent/'data/evaluation/sentiment_holdout.csv')
    except (pd.errors.ParserError,UnicodeDecodeError) as exc:
        st.error(f'Could not read the evaluation CSV: {exc}')
        st.stop()
    if evaluation_upload is None: st.caption('Default: frozen balanced 30-item author-reviewed holdout. It is reproducible but not an external benchmark.')
    if st.button('Evaluate selected sentiment model'):
        try:
            report=evaluate_sentiment_with_uncertainty(evaluation_data,'finbert' if backend.startswith('FinBERT') else 'lexicon')
            st.json(report)
            st.download_button('Download evaluation report',json.dumps(report,indent=2),'sentiment_evaluation.json','application/json')
        except (ValueError,RuntimeError,OSError) as exc: st.error(str(exc))
    st.write('Source audit for this brief')
    st.dataframe(audit_claims(brief['claims'],news),hide_index=True,alt='Mechanical citation audit for the evidence brief')
    st.caption('Citation validity and exact extraction are mechanical checks. Comparing factual support across generated briefs requires separate supported/unsupported/unclear human judgments, available through the research API.')
    st.subheader('Event taxonomy diagnostic')
    st.write('Evaluate the fixed event rules against a separate repository-authored labelled fixture.')
    if st.button('Evaluate event taxonomy',key='evaluate_event_taxonomy'):
        event_cases=pd.read_csv(Path(__file__).parent/'data/evaluation/event_taxonomy_cases.csv')
        st.json(evaluate_event_classifier(event_cases))
    st.caption('The 24-item event fixture checks mechanics and uncertainty states; it is not an external benchmark.')
