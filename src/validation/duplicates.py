from __future__ import annotations

import pandas as pd


def duplicate_ticket_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Return every row whose ticket_id occurs more than once, without mutation.

    This identifies ID collisions, not necessarily exact duplicate records.
    Null/blank ID policy remains the responsibility of the upstream contract.
    """
    return df[df["ticket_id"].duplicated(keep=False)].copy()
