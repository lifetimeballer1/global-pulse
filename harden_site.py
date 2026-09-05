#!/usr/bin/env python3
"""Apply safe, idempotent browser-facing hardening to public HTML."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
INDEX=ROOT/'index.html'
INTEL=ROOT/'intelligence-web.html'
CSP=("default-src 'self'; "
     "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
     "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
     "style-src 'self' 'unsafe-inline' https://unpkg.com; "
     "img-src 'self' data: blob: https:; font-src 'self' data: https:; "
     "connect-src 'self' https:; media-src 'self' https:; "
     "worker-src 'self' blob:; upgrade-insecure-requests")

def patch_document(path:Path,title:str,description:str):
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'\s*<meta http-equiv=["\']Content-Security-Policy["\'][^>]*>', '', text, flags=re.I)
    text=re.sub(r'\s*<meta name=["\']description["\'][^>]*>', '', text, flags=re.I)
    text=re.sub(r'\s*<meta property=["\']og:[^"\']+["\'][^>]*>', '', text, flags=re.I)
    text=text.replace('<meta name="theme-color" content="#050a10">','<meta name="theme-color" content="#050a10">\n<meta name="description" content="'+description+'">\n<meta property="og:type" content="website">\n<meta property="og:title" content="'+title+'">\n<meta property="og:description" content="'+description+'">\n<meta property="og:image" content="assets/icons/icon-512.png">\n<meta http-equiv="Content-Security-Policy" content="'+CSP+'">',1)
    text=re.sub(r'<title>.*?</title>',f'<title>{title}</title>',text,count=1,flags=re.S)
    # Keep Leaflet network dependencies non-blocking; the canonical map waits for them.
    text=re.sub(r'(<script\s+src=["\']https://unpkg\.com/leaflet[^>]+)(?<!defer)(\s*></script>)',r'\1 defer\2',text,flags=re.I)
    text=re.sub(r'(<script\s+src=["\']https://unpkg\.com/leaflet\.markercluster[^>]+)(?<!defer)(\s*></script>)',r'\1 defer\2',text,flags=re.I)
    path.write_text(text,encoding='utf-8')

def main():
    patch_document(INDEX,'Global Pulse — Global Conflict & Intelligence Monitor','Real-time global conflict, geopolitical risk, market context, hazards and evidence-linked open-source intelligence.')
    text=INTEL.read_text(encoding='utf-8')
    text=re.sub(r'\s*<meta name=["\']description["\'][^>]*>', '', text, flags=re.I)
    text=re.sub(r'\s*<meta property=["\']og:[^"\']+["\'][^>]*>', '', text, flags=re.I)
    text=text.replace('<meta name="theme-color" content="#03070b">','<meta name="theme-color" content="#03070b">\n<meta name="description" content="Evidence-linked Global Pulse intelligence relationship web for geopolitical, conflict and economic signals.">\n<meta property="og:type" content="website">\n<meta property="og:title" content="Global Pulse — Intelligence Web">\n<meta property="og:description" content="Evidence-linked geopolitical, conflict and economic relationships from public sources.">\n<meta property="og:image" content="assets/icons/icon-512.png">',1)
    INTEL.write_text(text,encoding='utf-8')
    print('SITE HARDENING APPLIED')

if __name__=='__main__':main()
