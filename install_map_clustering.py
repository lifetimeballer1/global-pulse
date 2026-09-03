#!/usr/bin/env python3
"""Install Leaflet marker clustering support without replacing the map renderer."""
from pathlib import Path

INDEX=Path(__file__).resolve().parent/"index.html"
START='<!-- GP-MARKER-CLUSTER-START -->'
END='<!-- GP-MARKER-CLUSTER-END -->'
BLOCK=f'''{START}
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" crossorigin="anonymous">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" crossorigin="anonymous">
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js" crossorigin="anonymous"></script>
{END}'''

def install():
    s=INDEX.read_text(encoding='utf-8')
    if START in s:
        a=s.index(START); b=s.index(END,a)+len(END); s=s[:a]+BLOCK+s[b:]
    else:
        s=s.replace('</head>',BLOCK+'\n</head>',1)
    INDEX.write_text(s,encoding='utf-8')
    print('Leaflet marker clustering support installed')

if __name__=='__main__': install()
