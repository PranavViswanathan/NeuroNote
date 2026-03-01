from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "api" / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))
