import uuid
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import Date, and_, cast, desc, func, literal
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import RelationshipDirection, selectinload
from sqlalchemy.sql.sqltypes import Integer
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from .schemas import CountByDateIn


ModelType = TypeVar('ModelType')


class BaseRepository(Generic[ModelType]):
    model: Type[ModelType]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find(self, id_: uuid.UUID, include: list | None = None) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id_)

        if include:
            stmt = stmt.options(*[selectinload(getattr(self.model, relation)) for relation in include])

        # noinspection PyTypeChecker
        result = await self.db.exec(stmt)
        return result.first()

    async def find_by(self, filters: dict, sort: str | None = None, include: list | None = None) -> list[ModelType]:
        stmt = await self._build_stmt(filters, sort, include)
        return stmt.all() # type: ignore

    async def find_one_by(self, filters: dict, include: list | None = None) -> ModelType | None:
        stmt = await self._build_stmt(filters, None, include)
        return stmt.first()

    async def find_one_projected_by(self, filters: dict, columns: list[str]) -> dict | None:
        stmt = await self._build_stmt_projected(filters, columns)
        row = stmt.first()
        if not row:
            return None
        return dict(zip(columns, row))

    async def find_projected_by(self, filters: dict, columns: list[str]) -> list:
        stmt = await self._build_stmt_projected(filters, columns)
        rows = stmt.all()
        if not rows:
            return []
        return [dict(zip(columns, row)) for row in rows]

    # pylint: disable=too-many-positional-arguments
    async def find_exact_by(
        self,
        field,
        value,
        filters: dict | None = None,
        include: list | None = None,
        exclude_ids: list | None = None,
    ) -> ModelType | None:
        column = getattr(self.model, field)
        extra_conditions = [column.ilike(value)]
        stmt = await self._build_stmt(
            filters=filters,
            include=include,
            extra_conditions=extra_conditions,
            execute=False
        )

        if exclude_ids:
            stmt = stmt.where(~self.model.id.in_(exclude_ids))

        # noinspection PyTypeChecker
        result = await self.db.exec(stmt)
        return result.first()

    async def create(
        self,
        values: dict[str, Any],
        *,
        ignore_unknown: bool = True,
        refresh: bool = True,
    ) -> ModelType:
        """
        Create and persist a new row from a dict.

        - Filters unknown keys by default (ignore_unknown=True).
          Set ignore_unknown=False to raise on unknown fields.
        - refresh=True ensures PK, defaults, and DB-generated fields are loaded.
        """
        # Keep only columns that actually exist on the model (avoid extra keys)
        mapper = sa_inspect(self.model)
        column_names = {c.key for c in mapper.columns}

        if ignore_unknown:
            data = {k: v for k, v in values.items() if k in column_names}
        else:
            unknown = set(values) - column_names
            if unknown:
                raise ValueError(f'Unknown fields for {self.model.__name__}: {sorted(unknown)}')
            data = dict(values)

        # Build instance (Pydantic v2 validation if available)
        if hasattr(self.model, 'model_validate'):
            instance = self.model.model_validate(data)  # type: ignore[attr-defined]
        else:
            instance = self.model(**data)  # fallback

        self.db.add(instance)
        await self.db.commit()

        if refresh:
            await self.db.refresh(instance)

        return instance

    async def update(
        self,
        entity_or_id: ModelType | uuid.UUID | int,
        values: dict[str, Any],
        refresh: bool = True,
        *,
        replace_more_info: bool = False,
    ) -> ModelType | None:
        """
        Update fields by id or instance.
        - Scalar columns in `values` are updated normally (PK excluded).
        - If `more_info` is present in `values`:
            - default behavior: shallow-merge into JSONB (server-side).
            - if `replace_more_info=True`: replace the entire JSON.
        - Returns updated instance (refreshed if you passed an instance and refresh=True) or None if not found.
        """
        # Resolve PK and optional instance
        if hasattr(entity_or_id, 'id') and not isinstance(entity_or_id, (uuid.UUID, int)):
            instance = entity_or_id
            pk_value = getattr(entity_or_id, 'id')
        else:
            instance = None
            pk_value = entity_or_id

        mapper = sa_inspect(self.model)
        pk_names = {pk.name for pk in mapper.primary_key}
        column_names = {c.key for c in mapper.columns}

        updates: dict[str, Any] = {}

        # Handle more_info specially if provided
        if 'more_info' in values:
            mi = values.get('more_info') or {}
            if not isinstance(mi, dict):
                raise ValueError('more_info must be a dict')

            if replace_more_info:
                # Full replace
                updates['more_info'] = mi
            else:
                # Server-side shallow merge: coalesce(more_info, '{}'::jsonb) || :mi::jsonb
                merged_expr = func.coalesce(
                    cast(self.model.more_info, JSONB),
                    literal({}, type_=JSONB)
                ).op('||')(literal(mi, type_=JSONB))
                updates['more_info'] = merged_expr

        # Add other scalar columns (exclude PK and more_info already handled)
        for k, v in values.items():
            if k == 'more_info':
                continue
            if k in column_names and k not in pk_names:
                updates[k] = v

        if not updates:
            # Nothing to update, return current row if exists
            stmt_get = select(self.model).where(self.model.id == pk_value)  # type: ignore
            res_get = await self.db.exec(stmt_get) # type: ignore
            return res_get.first()

        stmt = (
            update(self.model)
            .where(self.model.id == pk_value)  # type: ignore
            .values(**updates)
            .returning(self.model)
        )

        result = await self.db.exec(stmt)
        row = result.first()
        if not row:
            # Rollback to avoid leaving the transaction in a pending state
            await self.db.rollback()
            return None

        await self.db.commit()
        updated: ModelType = row[0] if isinstance(row, tuple) else row

        # Only refresh if caller passed an instance and asked for refresh
        if instance is not None and refresh:
            await self.db.refresh(instance)
            return instance

        return updated

    async def adjust_counter(
        self,
        entity_or_id: ModelType | uuid.UUID | int,
        field: str,
        amount: int = 1,
        *,
        refresh: bool = False,
    ) -> int:
        """
        Atomically increment an INTEGER-like column by `amount` and return the updated value.

        - `entity_or_id`: PK value (UUID|int) or a model instance.
        - `field`: column name to increment (must be an Integer/BigInteger).
        - `amount`: positive or negative int (decrement if negative).
        - If `refresh=True` and a model instance was provided, refresh that instance in-place.
        - Returns the new integer value. Returns 0 if the row doesn't exist (after rollback).
        """
        if not isinstance(amount, int):
            raise ValueError('amount must be an int')

        # Resolve PK and optional instance
        if hasattr(entity_or_id, 'id') and not isinstance(entity_or_id, (uuid.UUID, int)):
            instance = entity_or_id
            pk_value = getattr(entity_or_id, 'id')
        else:
            instance = None
            pk_value = entity_or_id

        # Validate column
        mapper = sa_inspect(self.model)
        col = {c.key: c for c in mapper.columns}.get(field)
        if col is None:
            raise ValueError(f'Invalid column: {field}')
        if not isinstance(col.type, Integer):
            raise ValueError(f'Column "{field}" must be an INTEGER-like type')

        # UPDATE ... SET field = COALESCE(field, 0) + :amount RETURNING field
        stmt = (
            update(self.model)
            .where(self.model.id == pk_value)  # type: ignore
            .values({field: func.coalesce(getattr(self.model, field), 0) + amount})
            .returning(getattr(self.model, field))
        )

        result = await self.db.exec(stmt)
        new_value = result.scalar_one_or_none()

        if new_value is None:
            # Rollback to avoid leaving the transaction in a pending state
            await self.db.rollback()
            return 0

        await self.db.commit()

        # Optionally keep the same instance fresh
        if instance is not None and refresh:
            await self.db.refresh(instance)

        return int(new_value)

    async def count_by(
        self,
        filters: dict[str, Any] | None = None,
        date_filter: CountByDateIn | None = None,
    ) -> int:
        """
        Return COUNT(*) applying optional filters and an optional date window.

        Date filtering compares by DATE (cast), inclusive:
            CAST(col AS DATE) BETWEEN start_date AND end_date
        """
        mapper = sa_inspect(self.model)
        columns_by_key = {c.key: c for c in mapper.columns}

        where_clauses: list[Any] = []

        # 1) Regular filters
        if filters:
            for k, v in filters.items():
                col = columns_by_key.get(k)
                if col is None:
                    continue
                if isinstance(v, (list, tuple, set)):
                    where_clauses.append(col.in_(list(v)))
                elif v is None:
                    where_clauses.append(col.is_(None))
                else:
                    where_clauses.append(col == v)

        # 2) Date filter using CAST(col AS DATE)
        if date_filter and date_filter.is_active():
            date_col_name = date_filter.resolve_column_name(set(columns_by_key.keys()))
            date_col = columns_by_key[date_col_name]

            date_only = cast(date_col, Date)
            where_clauses.append(date_only >= date_filter.start_date)
            where_clauses.append(date_only <= date_filter.end_date)

        # 3) Build and execute
        stmt = select(func.count()).select_from(self.model)
        if where_clauses:
            stmt = stmt.where(and_(*where_clauses))

        res = await self.db.exec(stmt)
        val = res.one_or_none()
        return int(val or 0)

    async def count_matrix_by(
        self,
        group_by: str,  # e.g., 'offer_id' or 'disposition_status'
        sub_group_by: str | None = None,  # None -> 1D; str -> 2D
        filters: dict[str, Any] | None = None,
        include_totals: bool = False,
        include_grand_total: bool = False,
    ) -> dict[Any, Any]:
        """
        Grouped counts (1D or 2D).

        - 1D (sub_group_by=None): returns {group_value: count, ..., 'Total': total}
        - 2D (sub_group_by given): returns
            {
              group_value: {sub_value: count, ..., 'Total': total_for_group},
              ...,
              ['GrandTotal': total_for_all_filters]  # only if include_grand_total=True
            }

        Notes:
        - 'Total' per group and 'GrandTotal' are computed via independent COUNT(*) with the same filters.
        - Unknown filter keys are ignored silently.
        """
        mapper = sa_inspect(self.model)
        cols = {c.key: c for c in mapper.columns}

        col1 = cols.get(group_by)
        if col1 is None:
            raise ValueError(f'Invalid group_by column: {group_by}')

        col2 = None
        if sub_group_by is not None:
            col2 = cols.get(sub_group_by)
            if col2 is None:
                raise ValueError(f'Invalid sub_group_by column: {sub_group_by}')

        # WHERE
        where_clauses = []
        if filters:
            for k, v in filters.items():
                c = cols.get(k)
                if c is None:
                    continue
                if isinstance(v, (list, tuple, set)):
                    where_clauses.append(c.in_(list(v)))
                elif v is None:
                    where_clauses.append(c.is_(None))
                else:
                    where_clauses.append(c == v)

        # 1D grouping
        if col2 is None:
            grouped_stmt = select(col1, func.count()).select_from(self.model).group_by(col1)
            if where_clauses:
                grouped_stmt = grouped_stmt.where(and_(*where_clauses))
            grouped_res = await self.db.exec(grouped_stmt)
            rows = grouped_res.all()  # [(group_value, count), ...]

            out: dict[Any, int] = {g: int(c) for g, c in rows}

            if include_totals:
                total_stmt = select(func.count()).select_from(self.model)
                if where_clauses:
                    total_stmt = total_stmt.where(and_(*where_clauses))
                total_res = await self.db.exec(total_stmt)
                total_value = total_res.first()
                out['total'] = int((total_value if total_value is not None else 0))

            return out

        # 2D grouping
        stmt = select(col1, col2, func.count()).select_from(self.model).group_by(col1, col2)
        if where_clauses:
            stmt = stmt.where(and_(*where_clauses))
        res = await self.db.exec(stmt)
        rows = res.all()  # [(group_value, sub_group_value, count), ...]

        out2d: dict[Any, dict[Any, int]] = {} #type: ignore
        for g1, g2, cnt in rows:
            bucket = out2d.setdefault(g1, {})
            bucket[g2] = int(cnt)

        if include_totals:
            # Real totals per group
            total_stmt = select(col1, func.count()).select_from(self.model).group_by(col1)
            if where_clauses:
                total_stmt = total_stmt.where(and_(*where_clauses))
            total_res = await self.db.exec(total_stmt)
            for g1, t in total_res.all():
                out2d.setdefault(g1, {})['total'] = int(t)

            if include_grand_total:
                grand_stmt = select(func.count()).select_from(self.model)
                if where_clauses:
                    grand_stmt = grand_stmt.where(and_(*where_clauses))
                grand_res = await self.db.exec(grand_stmt)
                grand_value = grand_res.first()
                out2d['grand_total'] = int((grand_value if grand_value is not None else 0)) #type: ignore

        return out2d

    async def first(self, order_col: str | None = None) -> ModelType | None:
        if order_col:
            col = getattr(self.model, order_col)
            stmt = select(self.model).order_by(col.asc()).limit(1)
        else:
            stmt = select(self.model).limit(1)

        res = await self.db.exec(stmt)
        return res.first()

    async def last(self, order_col: str = 'created_at') -> ModelType | None:
        col = getattr(self.model, order_col)
        stmt = select(self.model).order_by(col.desc()).limit(1)
        res = await self.db.exec(stmt)
        return res.first()

    async def _build_stmt(
        self,
        filters: dict | None = None,
        sort: str | None = None,
        include: list | None = None,
        extra_conditions: list | None = None,
        execute: bool = True,
    ):
        conditions: list[Any] = []

        if extra_conditions:
            conditions.extend(extra_conditions)

        if filters:
            for k, v in filters.items():
                if not hasattr(self.model, k):
                    raise ValueError(f"Invalid filter: '{k}' is not a column of {self.model.__name__}")
                conditions.append(getattr(self.model, k) == v)

        stmt = select(self.model).where(and_(*conditions))

        if include:
            stmt = stmt.options(*[selectinload(getattr(self.model, relation)) for relation in include])

        if sort:
            is_desc = sort.startswith('-')
            sort_field = sort.lstrip('-')

            column = getattr(self.model, sort_field)
            stmt = stmt.order_by(desc(column) if is_desc else column)

        if execute:
            # noinspection PyTypeChecker
            return await self.db.exec(stmt)

        return stmt

    async def _build_stmt_projected(self, filters: dict, columns: list[str]):
        column_exprs = [
            getattr(self.model, col) for col in columns if hasattr(self.model, col)
        ]
        if not column_exprs:
            raise ValueError('No valid columns provided')

        conditions = []
        for k, v in filters.items():
            if not hasattr(self.model, k):
                raise ValueError(f"Invalid filter: '{k}' is not a column of {self.model.__name__}")
            conditions.append(getattr(self.model, k) == v)

        stmt = select(*column_exprs).where(and_(*conditions))

        # noinspection PyTypeChecker
        return await self.db.exec(stmt)

    async def delete(self, id_value: uuid.UUID, commit: bool = True) -> int:
        obj = await self.db.get(self.model, id_value)
        if not obj:
            return 0

        visited: set[tuple[type, uuid.UUID | None]] = set()
        await self._delete_children(obj, visited)

        if commit:
            await self.db.commit()
        return 1

    async def _delete_children(self, obj: ModelType, visited: set[tuple[type, uuid.UUID | None]]) -> None:
        """
        Recursively deletes children discovered via Relationships (no DB ON DELETE).
        Avoids async lazy-load by explicit refresh(attribute_names=[rel.key]).
        Skips MANYTOONE to not walk 'up' to parents.
        """
        obj_id = getattr(obj, 'id', None)
        key = (type(obj), obj_id)
        if key in visited:
            return
        visited.add(key)

        mapper = type(obj).__mapper__

        for rel in mapper.relationships:
            if rel.viewonly:
                continue
            # Skip going "up" to parent to avoid deleting ancestors
            if rel.direction is RelationshipDirection.MANYTOONE:
                continue

            # Explicitly load this relationship to avoid MissingGreenlet
            await self.db.refresh(obj, attribute_names=[rel.key])

            related = getattr(obj, rel.key, None)
            if related is None:
                continue

            if rel.uselist:
                # one-to-many / many-to-many
                for child in list(related):
                    await self._delete_children(child, visited)
                    await self.db.delete(child)
            else:
                # one-to-one (or many-to-one from the other side)
                child = related
                await self._delete_children(child, visited)
                await self.db.delete(child)

        # Delete the parent last
        await self.db.delete(obj)
