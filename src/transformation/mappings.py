"""Mappings métier pilotés par les référentiels Google Sheets."""
from __future__ import annotations

import re
import unicodedata
import pandas as pd


def key(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def build_mapping(df: pd.DataFrame, source_col: str, target_col: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        source, target = row.get(source_col), row.get(target_col)
        if pd.isna(source) or pd.isna(target) or not str(source).strip() or not str(target).strip():
            continue
        k = key(source); v = str(target).strip()
        if k in mapping and mapping[k] != v:
            raise ValueError(f"Mapping contradictoire pour {source!r}: {mapping[k]!r} vs {v!r}")
        mapping[k] = v
    return mapping


def map_value(value: object, mapping: dict[str, str]) -> tuple[str | None, bool]:
    k = key(value)
    if not k:
        return None, False
    result = mapping.get(k)
    return result, result is not None


def normalize_technician(value: object) -> str | None:
    k = key(value)
    return {"loubna": "Loubna", "sofiane aoues": "Sofiane Aoues"}.get(k, str(value).strip() if k else None)


def normalize_priority(value: object) -> str | None:
    k = key(value)
    return {"basse": "Basse", "faible": "Basse", "moyen": "Moyenne", "moyenne": "Moyenne", "élevé": "Haute", "elevé": "Haute", "eleve": "Haute", "urgent": "Haute", "haute": "Haute"}.get(k)
