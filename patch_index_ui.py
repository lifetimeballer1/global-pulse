from pathlib import Path

# Legacy compatibility patch. The current UI hardening lives in apply_ui_patch.py.
# Keep this step idempotent so scheduled refreshes can never fail because an
# earlier UI patch already changed the target markup.
p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Ensure the base modal backdrop is opaque even before the hardening patch runs.
s = s.replace(
    'background:rgba(0,0,0,.6);z-index:90',
    'background:#050a10;z-index:90;opacity:1',
)

p.write_text(s, encoding='utf-8')
print('Legacy UI compatibility patch applied safely')
