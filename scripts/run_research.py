"""python scripts/run_research.py [--live] [--finbert] [--labels labelled.csv]"""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
from ingestion import fetch_official_feeds
from modelling import score_news
from evidence import evidence_brief,export_bundle
from evaluation import evaluate_sentiment

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true');parser.add_argument('--finbert',action='store_true')
    parser.add_argument('--labels',type=Path,default=Path('data/evaluation/diagnostic_cases.csv'))
    parser.add_argument('--output',type=Path,default=Path('outputs'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    reports=[evaluate_sentiment(pd.read_csv(args.labels),'lexicon')]
    if args.finbert:reports.append(evaluate_sentiment(pd.read_csv(args.labels),'finbert'))
    (args.output/'sentiment_evaluation.json').write_text(json.dumps(reports,indent=2))
    print(json.dumps(reports,indent=2))
    if args.live:
        news,diagnostics=fetch_official_feeds()
        print(json.dumps(diagnostics,indent=2))
        (args.output/'feed_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
        if news.empty:raise SystemExit('No official feed succeeded; no synthetic substitution.')
        news=score_news(news);brief=evidence_brief(news)
        (args.output/'market_research.zip').write_bytes(export_bundle(news,brief,{'diagnostics':diagnostics}))
