from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, Boolean


class QueryBuilder:
    def __init__(self, db: AsyncSession, model, params):
        self.model = model
        self.stmt = None
        self.params = params
        self.db = db

    def init(self):
        filters = {}
        if ('filters' in self.params) and ('equals' in self.params['filters']):
            filters = self.params['filters']['equals']
            if 'init' in self.params['filters']:
                filters = {**filters, **self.params['filters']['init']}

        self.stmt = select(self.model)
        self.apply_filters(filters)
        self.apply_sort()

        if self.params['include']:
            relationships = self.params['include']
            self.stmt = self.stmt.options(*[selectinload(getattr(self.model, relation)) for relation in relationships])

        return self

    def apply_filters(self, filters: dict[str, any]):
        for key, value in filters.items():
            if value:
                column = getattr(self.model, key, None)
                if column:
                    if isinstance(value, list):
                        self.stmt = self.stmt.where(column.in_(value))
                    else:
                        if hasattr(column, 'type') and isinstance(column.type, Boolean):
                            value = self.parse_bool(value)

                        if value is not None:
                            self.stmt = self.stmt.where(column == value)

    def apply_sort(self):
        if self.params['sort']:
            col = self.params['sort'][0]['col']
            dir_ = self.params['sort'][0]['dir']

            column = getattr(self.model, col, None)
            if column:
                if dir_ == 'desc':
                    self.stmt = self.stmt.order_by(column.desc())
                else:
                    self.stmt = self.stmt.order_by(column)

    async def get(self, native = False):
        result = await self.db.exec(self.stmt)
        if native:
            return result.all()
        else:
            rows = result.all()
            # Check only the first record, if available
            if rows and (not hasattr(rows[0], 'to_dict') or not callable(getattr(rows[0], 'to_dict', None))):
                return rows

            # If the first record has `to_dict()`, return the transformed list
            return [o.to_dict() for o in rows]

    async def total(self) -> int:
        count_stmt = select(func.count()).select_from(self.stmt)
        total_result = await self.db.exec(count_stmt)
        return total_result.one()

    @staticmethod
    def parse_bool(value: str | int | bool | None) -> bool | None:
        """
        Safely parses different representations of boolean values into Python bools.
        Returns None if the input is invalid or empty.

        Supported values:
        - True, 'true', '1', 1   → True
        - False, 'false', '0', 0 → False
        - None, '', '  '         → None
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ('true', '1'):
                return True
            if value in ('false', '0'):
                return False
        return None
