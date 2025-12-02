from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class Result:
    original: pd.DataFrame
    inserted: Optional[pd.DataFrame] = None
    updated: Optional[pd.DataFrame] = None
    deleted: Optional[pd.DataFrame] = None

    def __post_init__(self):
        if self.inserted is None:
            self.inserted = pd.DataFrame()
        if self.updated is None:
            self.updated = pd.DataFrame()
        if self.deleted is None:
            self.deleted = pd.DataFrame()

    @property
    def total_original(self) -> int:
        return len(self.original)

    @property
    def total_inserted(self) -> int:
        return len(self.inserted)

    @property
    def total_updated(self) -> int:
        return len(self.updated)

    @property
    def total_deleted(self) -> int:
        return len(self.deleted)

    @property
    def has_changes(self) -> bool:
        return not (self.inserted.empty and self.updated.empty and self.deleted.empty)
