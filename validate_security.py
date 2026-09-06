#!/usr/bin/env python3
"""Fail-closed security/privacy checks for Global Pulse CI."""
from __future__ import annotations
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
TRACKING=re.compile(r"google-analytics|googletagmanager|gtag\(|analytics\.js|sentry\.io|hotjar|mixpanel|segment\.com|clarity\.ms",re.I)
CLIENT_TELEMETRY=re.compile(r"navigator\.sendBeacon|new\s+Image\s*\(|fetch\s*\([^)]*(telemetry|analytics|track)",re.I)
SECRET_LIKE=re.compile(r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]",re.I)
CSP_REQUIRED=("default-src 'self'","base-uri 'self'","object-src 'none'","frame-ancestors 'none'","script-src","style-src","img-src","connect-src","worker-src","upgrade-insecure-requests")

def extract_csp(text:str):
 m=re.search(r'<meta\s+http-equiv=["\']Content-Security-Policy["\']\s+content="([^"]+)"',text,re.I)
 if not m:m=re.search(r"<meta\s+http-equiv=['\"]Content-Security-Policy['\"]\s+content='([^']+)'",text,re.I)
 return m.group(1) if m else None

def check_html(path:Path):
 text=path.read_text(encoding='utf-8')
 assert not TRACKING.search(text),f"Unexpected analytics/tracking code in {path.name}"
 assert not CLIENT_TELEMETRY.search(text),f"Unexpected client telemetry in {path.name}"
 csp=extract_csp(text); assert csp,f"CSP missing from {path.name}"
 for directive in CSP_REQUIRED:assert directive in csp,f"{directive} missing from {path.name} CSP"
 assert 'https:' in csp,f"external HTTPS policy missing from {path.name} CSP"
 assert 'strict-origin-when-cross-origin' in text,f"referrer policy missing from {path.name}"
 print('PASS browser security contract',path.name)

def main():
 check_html(ROOT/'index.html');check_html(ROOT/'intelligence-web.html')
 for path in (ROOT/'.github/workflows').glob('*.yml'):
  text=path.read_text(encoding='utf-8')
  assert not SECRET_LIKE.search(text),f"Secret-like literal found in {path}"
  assert 'pull_request_target' not in text,f"Unsafe pull_request_target in {path}"
 print('PASS workflow trigger/secret policy')
 client_files=list(ROOT.glob('*.js'))+list((ROOT/'js').rglob('*.js'))
 for path in client_files:
  text=path.read_text(encoding='utf-8',errors='ignore')
  assert not CLIENT_TELEMETRY.search(text),f"Client telemetry pattern in {path}"
 print(f'PASS client privacy scan ({len(client_files)} assets)')
 hardener=(ROOT/'harden_site.py').read_text(encoding='utf-8')
 assert 'Content-Security-Policy' in hardener and "frame-ancestors 'none'" in hardener
 assert 'strict-origin-when-cross-origin' in hardener
 print('PASS hardening source contract')
 print('SECURITY VALIDATION PASSED')

if __name__=='__main__':main()
