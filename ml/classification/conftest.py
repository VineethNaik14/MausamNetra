"""
Ensures `src/` is importable as a top-level package (predict, config, preprocess)
both when running pytest and when opening files directly in an editor.

Place this file at: ml/classification/conftest.py
(i.e. the same level as src/, tests/, api/ - NOT inside tests/)
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
