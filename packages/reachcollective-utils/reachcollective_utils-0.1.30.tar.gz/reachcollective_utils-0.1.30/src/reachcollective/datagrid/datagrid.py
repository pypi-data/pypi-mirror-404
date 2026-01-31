from fastapi import Request
from sqlmodel.ext.asyncio.session import AsyncSession

from .paginator import Paginator
from .query_builder import QueryBuilder
from .query_params import QueryParams


class DataGrid:
    def __init__(self, db: AsyncSession, model, request: Request):

        self.model = model
        self.db = db
        self.params = {}

        self.qp: QueryParams = QueryParams(request)
        self.qb: QueryBuilder | None = None

    def init(self):
        self.params = self.qp.get()
        self.qb = QueryBuilder(self.db, self.model, self.params).init()

        return self

    async def get(self):
        match self.qp.view:
            case 'paginate':
                return await Paginator(self.qb, self.qp).get()
            case 'count':
                return await self.qb.total()
            case _:
                return await self.qb.get()
