from __future__ import annotations
import pandas as pd


def duplicate_ticket_ids(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["ticket_id"].duplicated(keep=False)].copy()
