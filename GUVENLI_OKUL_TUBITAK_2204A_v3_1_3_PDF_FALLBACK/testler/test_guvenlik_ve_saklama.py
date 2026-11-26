"""Temel erişim ve saklama ilkelerinin kaynak kodda korunmasını denetler."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
import db

ROOT = Path(__file__).resolve().parents[1]


def _function_node(source: str, name: str):
    tree = ast.parse(source)
    return next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


@pytest.mark.parametrize("function_name", [
    "sayfa_inceleme",
    "sayfa_istatistikler",
    "sayfa_trend",
    "sayfa_etki_merkezi",
    "sayfa_takvim",
    "sayfa_bildirim_merkezi",
    "sayfa_yonetim_gunlugu",
    "sayfa_pdf_rapor",
    "sayfa_yedekleme",
])
def test_yonetim_sayfalari_yonetici_kontrolu_icerir(function_name):
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    node = _function_node(source, function_name)
    calls = [
        item for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == "yonetici_gerekli"
    ]
    assert calls, f"{function_name} yönetici kontrolü çağırmalı."


def test_sureye_bagli_kayit_silme_kapali():
    with pytest.raises(RuntimeError, match="kayıt silme devre dışıdır"):
        db.sonuclanmis_kayitlari_sil(360, "test")
