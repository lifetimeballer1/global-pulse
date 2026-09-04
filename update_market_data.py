#!/usr/bin/env python3
"""Collect near-real-time market indicators without requiring user API keys."""
from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parent;SNAP=ROOT/'data'/'snapshot.json';UA='Mozilla/5.0 (compatible; GlobalPulse/11.0)'
WATCH=[('S&P 500','^GSPC','index','USD',2),('Dow Jones','^DJI','index','USD',2),('Nasdaq Composite','^IXIC','index','USD',2),('Nasdaq 100','^NDX','index','USD',2),('Russell 2000','^RUT','index','USD',2),('VIX','^VIX','volatility','USD',2),('WTI Crude','CL=F','commodity','USD',2),('Gold','GC=F','commodity','USD',2),('Bitcoin','BTC-USD','crypto','USD',0),('EUR / USD','EURUSD=X','fx','USD',4),('USD / JPY','JPY=X','fx','JPY',2),('U.S. 10Y Yield','^TNX','rates','%',2),('FTSE 100','^FTSE','index','GBP',2),('DAX','^GDAXI','index','EUR',2),('Nikkei 225','^N225','index','JPY',2),('Shanghai Composite','000001.SS','index','CNY',2),('Hang Seng','^HSI','index','HKD',2),('Nifty 50','^NSEI','index','INR',2),('Sensex','^BSESN','index','INR',2),('Apple','AAPL','equity','USD',2),('Microsoft','MSFT','equity','USD',2),('NVIDIA','NVDA','equity','USD',2),('Amazon','AMZN','equity','USD',2),('Alphabet','GOOGL','equity','USD',2),('Meta','META','equity','USD',2),('Tesla','TSLA','equity','USD',2)]
def now():return datetime.now(timezone.utc).isoformat()
def fetch_quote(symbol):
 last=None
 for host in ('query1.finance.yahoo.com','query2.finance.yahoo.com'):
  try:
   u=f'https://{host}/v8/finance/chart/{quote(symbol,safe="")}?range=1d&interval=1m&includePrePost=true&events=history';req=Request(u,headers={'User-Agent':UA,'Accept':'application/json'})
   with urlopen(req,timeout=8) as r:p=json.loads(r.read().decode())
   result=((p.get('chart') or {}).get('result') or [None])[0]
   if not result:raise RuntimeError('no chart result')
   meta=result.get('meta') or {};ts=result.get('timestamp') or [];q=((result.get('indicators') or {}).get('quote') or [{}])[0];cl=q.get('close') or [];pairs=[(int(t),float(v)) for t,v in zip(ts,cl) if v is not None]
   if not pairs:raise RuntimeError('no intraday candles')
   candle_ts,price=pairs[-1];previous=meta.get('chartPreviousClose') or meta.get('previousClose') or price;previous=float(previous);change=price-previous;pct=change/previous*100 if previous else 0
   state=str(meta.get('marketState') or '').upper();status='live' if symbol=='BTC-USD' or state in {'REGULAR','PRE','POST'} else 'closed'
   timestamp=datetime.fromtimestamp(candle_ts,tz=timezone.utc).isoformat()
   return {'price':price,'previousClose':previous,'change':change,'changePercent':pct,'marketTime':timestamp,'marketState':state,'currency':meta.get('currency'),'exchange':meta.get('fullExchangeName') or meta.get('exchangeName'),'endpoint':host,'interval':'1m','provider':'Yahoo Finance','quoteSource':'latest intraday candle'}
  except Exception as e:last=e
 raise RuntimeError(str(last) if last else 'all public market endpoints failed')
def collect(item):
 try:return item,fetch_quote(item[1]),None
 except Exception as e:return item,None,f'{type(e).__name__}: {e}'[:180]
def main():
 data=json.loads(SNAP.read_text(encoding='utf-8')) if SNAP.exists() else {};prev=data.get('marketData') if isinstance(data.get('marketData'),dict) else {};old={x.get('symbol'):x for x in prev.get('indicators',[]) if isinstance(x,dict)};vals={};errors=[]
 with ThreadPoolExecutor(max_workers=8) as pool:
  for f in as_completed([pool.submit(collect,x) for x in WATCH]):
   item,q,e=f.result();name,symbol,kind,unit,dec=item
   if q:q.update({'name':name,'symbol':symbol,'type':kind,'unit':unit,'decimals':dec,'status':q.get('status'),'source':'Yahoo Finance public chart (1m)','checkedAt':now()});vals[symbol]=q
   else:
    if symbol in old:x=dict(old[symbol]);x['status']='stale';x['checkedAt']=now();vals[symbol]=x
    errors.append({'symbol':symbol,'error':e})
 indicators=[vals[s] for _,s,*_ in WATCH if s in vals];market={'updatedAt':now(),'source':'Yahoo Finance public chart (1m)','provider':'Yahoo Finance','noApiKey':True,'quoteInterval':'1m','refreshMinutes':5,'indicators':indicators,'errors':errors,'liveCount':sum(x.get('status')=='live' for x in indicators),'closedCount':sum(x.get('status')=='closed' for x in indicators),'staleCount':sum(x.get('status')=='stale' for x in indicators)};data['marketData']=market;SNAP.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f"MARKET DATA: live={market['liveCount']} closed={market['closedCount']} stale={market['staleCount']} errors={len(errors)}")
if __name__=='__main__':main()
