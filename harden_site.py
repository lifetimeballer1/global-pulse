#!/usr/bin/env python3
"""Apply safe, idempotent browser-facing hardening to public HTML."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
INDEX=ROOT/'index.html'
INTEL=ROOT/'intelligence-web.html'
CSP=("default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
     "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
     "style-src 'self' 'unsafe-inline' https://unpkg.com; img-src 'self' data: blob: https:; "
     "font-src 'self' data: https:; connect-src 'self' https:; media-src 'self' https:; "
     "worker-src 'self' blob:; upgrade-insecure-requests")

def patch_document(path:Path,title:str,description:str):
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'\s*<meta http-equiv=["\']Content-Security-Policy["\'][^>]*>', '', text, flags=re.I)
    text=re.sub(r'\s*<meta name=["\']description["\'][^>]*>', '', text, flags=re.I)
    text=re.sub(r'\s*<meta property=["\']og:[^"\']+["\'][^>]*>', '', text, flags=re.I)
    text=re.sub(r'\s*<meta name=["\']referrer["\'][^>]*>', '', text, flags=re.I)
    insertion=(f'<meta name="description" content="{description}">\n'
               f'<meta name="referrer" content="strict-origin-when-cross-origin">\n'
               f'<meta property="og:type" content="website">\n<meta property="og:title" content="{title}">\n'
               f'<meta property="og:description" content="{description}">\n'
               '<meta property="og:image" content="assets/icons/icon-512.png">\n'
               f'<meta http-equiv="Content-Security-Policy" content="{CSP}">')
    marker='<meta name="theme-color" content="#050a10">'
    if marker in text:
        text=text.replace(marker,marker+'\n'+insertion,1)
    else:
        text=text.replace('<head>','<head>\n'+insertion,1)
    text=re.sub(r'<title>.*?</title>',f'<title>{title}</title>',text,count=1,flags=re.S)
    text=re.sub(r'(<script\s+src=["\']https://unpkg\.com/leaflet[^>]+)(?<!defer)(\s*></script>)',r'\1 defer\2',text,flags=re.I)
    text=re.sub(r'(<script\s+src=["\']https://unpkg\.com/leaflet\.markercluster[^>]+)(?<!defer)(\s*></script>)',r'\1 defer\2',text,flags=re.I)
    path.write_text(text,encoding='utf-8')

def main():
    patch_document(INDEX,'Global Pulse — Global Conflict & Intelligence Monitor','Real-time global conflict, geopolitical risk, market context, hazards and evidence-linked open-source intelligence.')
    patch_document(INTEL,'Global Pulse — Intelligence Web','Evidence-linked Global Pulse intelligence relationship web for geopolitical, conflict and economic signals.')
    text=INTEL.read_text(encoding='utf-8')
    text=text.replace('#647b8d','#91a4b8')
    INTEL.write_text(text,encoding='utf-8')
    print('SITE HARDENING APPLIED')

if __name__=='__main__':main()
