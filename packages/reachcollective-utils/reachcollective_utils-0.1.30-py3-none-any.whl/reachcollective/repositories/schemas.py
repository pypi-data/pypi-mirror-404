from datetime import date, timedelta
from pydantic import BaseModel, model_validator


class CountByDateIn(BaseModel):
    """
    Date filter for count_by() using DATE-only comparison.
    Assumes the underlying column is a datetime and casts to DATE.

    Assumptions:
    - Caller guarantees end_date >= start_date when both are provided.
    - If lookback_days is provided (days), window is [today - (lookback_days - 1), today] inclusive.
    """

    date_column: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    lookback_days: int | None = None

    @model_validator(mode='after')
    def _normalize(self) -> 'CountByDateIn':
        # No swapping; we assume end_date >= start_date if both come in.
        if (self.start_date is None or self.end_date is None) and self.lookback_days:
            today = date.today()
            self.start_date = today - timedelta(days=max(self.lookback_days, 1) - 1)
            self.end_date = today
        return self

    def is_active(self) -> bool:
        return self.start_date is not None and self.end_date is not None

    def resolve_column_name(self, available_keys: set[str]) -> str:
        if self.date_column and self.date_column in available_keys:
            return self.date_column
        if 'created_at' in available_keys:
            return 'created_at'
        if 'created_date' in available_keys:
            return 'created_date'
        raise ValueError('No suitable date column found. Provide date_column or add created_at/created_date.')
