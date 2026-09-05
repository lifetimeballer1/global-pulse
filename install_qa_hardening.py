#!/usr/bin/env python3
"""Install the final browser QA/performance layer into the generated dashboard."""
from pathlib import Path
import re

INDEX=Path(__file__).resolve().parent/'index.html'
TAG='<script src="global_pulse_qa.js?v=1" defer></script>'
LAZY_OLD=r'const wait=\(\)=>\{let n=0;const t=setInterval\(\(\)=>\{if\(boot\(\)\|\|\+\+n>200\)clearInterval\(t\)\},100\)\};\n  if\(document\.readyState==="loading"\)document\.addEventListener\("DOMContentLoaded",wait\);else wait\(\);'
LAZY_NEW='''const wait=()=>{const target=document.getElementById("map");if(!target)return;let started=false;const start=()=>{if(started)return;started=true;let n=0;const t=setInterval(()=>{if(boot()||++n>200)clearInterval(t)},100)};if("IntersectionObserver" in window){const o=new IntersectionObserver(es=>{if(es.some(e=>e.isIntersecting)){o.disconnect();start()}},{rootMargin:"300px"});o.observe(target)}else start()};
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",wait);else wait();'''

def main():
    s=INDEX.read_text(encoding='utf-8')
    s=re.sub(r'\s*<script[^>]*src=["\']global_pulse_qa\.js(?:\?[^"\']*)?["\'][^>]*>\s*</script>', '', s, flags=re.I)
    s,n=re.subn(LAZY_OLD,LAZY_NEW,s,count=1)
    if n:
        print('LAZY MAP INSTALLATION APPLIED')
    if '</body>' not in s: raise RuntimeError('index.html has no closing body tag')
    s=s.replace('</body>',TAG+'\n</body>',1)
    INDEX.write_text(s,encoding='utf-8')
    print('QA HARDENING INSTALLED')

if __name__=='__main__': main()
