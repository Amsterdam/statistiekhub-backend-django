from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Result:
    original: pd.DataFrame
    inserted: pd.DataFrame = field(default_factory=pd.DataFrame)
    updated: pd.DataFrame = field(default_factory=pd.DataFrame)
    deleted: pd.DataFrame = field(default_factory=pd.DataFrame)

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
