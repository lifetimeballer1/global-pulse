from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Update 2 is retired. The original Global Pulse map already renders
# window.DATA.markers, so the safest architecture is to leave that controller
# untouched and only remove artifacts from the retired layer.
s = re.sub(r'\n<style id="gp-map-pro-css">.*?</style>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<script id="gp-map-pro-js">.*?</script>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<div[^>]*id="gpMapTools"[^>]*>.*?</div>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<div[^>]*id="gpMapLegend"[^>]*>.*?</div>\n?', '\n', s, flags=re.S)
s = re.sub(r'<section[^>]*id="gpBrief"[^>]*>.*?</section>', '', s, flags=re.S)

p.write_text(s, encoding='utf-8')
print('Original Global Pulse map preserved; retired Update 2 layer removed')
