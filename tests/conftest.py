import sys
from pathlib import Path

# src layout: ensure `import visclick` works without pip install -e
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
