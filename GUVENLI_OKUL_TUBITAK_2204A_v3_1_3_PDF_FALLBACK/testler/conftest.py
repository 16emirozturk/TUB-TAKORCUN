from __future__ import annotations

import sys
from pathlib import Path

# pytest'i depo kökünden veya testler/ klasöründen başlatınca modüller bulunabilsin.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import db


@pytest.fixture
def temiz_veritabani(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_YOLU", tmp_path / "test.db")
    db.hazirla()
    db.anonim_hazirla()
    yield
