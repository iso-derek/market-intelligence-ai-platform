"""Timestamped public RSS/Atom ingestion with explicit source provenance."""
from email.utils import parsedate_to_datetime
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import xml.etree.ElementTree as ET
import pandas as pd
import requests

FEEDS={
    'Federal Reserve monetary policy':'https://www.federalreserve.gov/feeds/press_monetary.xml',
    'ECB announcements':'https://www.ecb.europa.eu/rss/press.html',
}


def canonical_url(value):
    p=urlsplit(str(value).strip())
    if p.scheme not in {'https','http'} or not p.hostname or p.username or p.password:
        raise ValueError('Source links must be public HTTP(S) URLs without credentials.')
    query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid'}]
    return urlunsplit((p.scheme,p.netloc.lower(),p.path,urlencode(query),''))


def normalise_news(raw, retrieved_at=None):
    frame=raw.copy()
    now=pd.Timestamp.now(tz='UTC') if retrieved_at is None else pd.to_datetime(retrieved_at,utc=True)
    if 'headline' not in frame: raise ValueError('News must include headline.')
    if 'published_at' not in frame:
        if 'date' not in frame: raise ValueError('News must include published_at timestamps.')
        frame['published_at']=frame['date']
    frame['headline']=frame.headline.fillna('').astype(str).str.replace(r'\s+',' ',regex=True).str.strip()
    def publication_time(value):
        if isinstance(value,str):
            try:
                return pd.Timestamp(parsedate_to_datetime(value)).tz_convert('UTC')
            except (ValueError, TypeError):
                pass
        return pd.to_datetime(value,utc=True,errors='coerce')
    frame['published_at']=pd.to_datetime(frame.published_at.map(publication_time),utc=True)
    if frame.published_at.isna().any() or frame.headline.eq('').any():
        raise ValueError('Every article needs a non-empty headline and valid publication timestamp.')
    frame['retrieved_at']=pd.to_datetime(frame.get('retrieved_at',now),utc=True,errors='coerce',format='mixed')
    frame['available_at']=pd.to_datetime(frame.get('available_at',frame.retrieved_at),utc=True,errors='coerce',format='mixed')
    if frame[['retrieved_at','available_at']].isna().any().any(): raise ValueError('Invalid availability/retrieval timestamp.')
    if (frame.available_at<frame.published_at).any(): raise ValueError('Availability cannot precede publication.')
    for c,value in {'company':'Macro economy','ticker':'MACRO','sector':'Economy','topic':'Policy','source':'Uploaded source','synthetic':False,'url':''}.items():
        if c not in frame: frame[c]=value
        frame[c]=frame[c].fillna(value)
    if frame.synthetic.dtype!=bool:
        values=frame.synthetic.astype(str).str.lower()
        if not values.isin(['true','false','1','0']).all(): raise ValueError('Synthetic flag must be true or false.')
        frame['synthetic']=values.isin(['true','1'])
    frame['url']=[canonical_url(u) if str(u).strip() else '' for u in frame.url]
    frame['article_id']=[hashlib.sha256((u+'\n'+h+'\n'+str(t)).encode()).hexdigest()[:16] for u,h,t in zip(frame.url,frame.headline,frame.published_at)]
    frame['date']=frame.published_at.dt.floor('D')
    frame=frame.sort_values('available_at').drop_duplicates('article_id',keep='first')
    # Duplicate text counts once even if repeated/syndicated under another URL.
    frame['_text_key']=frame.headline.str.casefold()
    frame=frame.drop_duplicates('_text_key').drop(columns='_text_key')
    frame['month']=frame.published_at.dt.strftime('%Y-%m')
    return frame.reset_index(drop=True)


def parse_feed(xml,source,retrieved_at=None):
    if len(xml)>5_000_000 or b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
        raise ValueError('Oversized feed or unsupported XML entity declaration.')
    root=ET.fromstring(xml)
    entries=[e for e in root.iter() if e.tag.rsplit('}',1)[-1] in {'item','entry'}]
    rows=[]; skipped=0
    for entry in entries:
        fields={c.tag.rsplit('}',1)[-1]:c for c in entry}
        def value(*names):
            return next((''.join(fields[n].itertext()).strip() for n in names if n in fields),'')
        link=value('link')
        if not link:
            for child in entry:
                if child.tag.rsplit('}',1)[-1]=='link' and child.attrib.get('rel','alternate')=='alternate':
                    link=child.attrib.get('href',''); break
        try:
            row={'headline':value('title'),'url':canonical_url(link),
                 'published_at':value('pubDate','published','updated'),'source':source}
            rows.append(normalise_news(pd.DataFrame([row]),retrieved_at))
        except (ValueError,TypeError): skipped+=1
    if not rows: raise ValueError('Feed contains no valid dated, linked articles.')
    frame=normalise_news(pd.concat(rows,ignore_index=True),retrieved_at)
    return frame,{'source':source,'parsed':len(frame),'skipped':skipped,'feed_sha256':hashlib.sha256(xml).hexdigest()}


def fetch_official_feeds(names=None):
    rows=[]; diagnostics=[]
    for name in (list(FEEDS) if names is None else names):
        if name not in FEEDS: raise ValueError('Select a supported official feed.')
        try:
            response=requests.get(FEEDS[name],timeout=20,headers={'User-Agent':'MarketIntelligenceResearch/1.0'})
            response.raise_for_status()
            frame,meta=parse_feed(response.content,name)
            rows.append(frame); diagnostics.append({**meta,'status':'ok','feed_url':FEEDS[name]})
        except (requests.RequestException,ValueError,ET.ParseError) as exc:
            diagnostics.append({'source':name,'status':'failed','error':str(exc),'feed_url':FEEDS[name]})
    frame=normalise_news(pd.concat(rows,ignore_index=True)) if rows else pd.DataFrame()
    return frame,diagnostics
