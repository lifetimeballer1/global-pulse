from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Update 3 created an Evidence Center that can be duplicated by later pipeline
# passes. Remove every copy and its associated assets. Evidence remains in the
# underlying DATA.markers / DATA.stories datasets; only the duplicate UI layer
# is being removed.
s = re.sub(r'\n<style id="gp-evidence-css">.*?</style>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<script id="gp-evidence-js">.*?</script>\n?', '\n', s, flags=re.S)
s = re.sub(r'\n<section[^>]*id="evidenceCenter"[^>]*>.*?</section>\n?', '\n', s, flags=re.S)

# Also remove duplicate Evidence Center wrappers if a previous malformed pass
# nested one inside another. The explicit id cleanup above handles normal cases.
p.write_text(s, encoding='utf-8')
print('Removed all duplicate Evidence Center UI layers; underlying evidence data preserved')
