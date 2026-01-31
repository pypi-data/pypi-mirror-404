import math

from .query_builder import QueryBuilder
from .query_params import QueryParams


class Paginator:
    def __init__(self, query_builder: QueryBuilder, query_params: QueryParams):
        self.r = self.get_template()
        self.qp = query_params
        self.qb = query_builder

    @staticmethod
    def get_template() -> dict:
        return {
            'current_page': 1,
            'data': [],
            'total': None,
            'per_page': None,
            'total_pages': None
        }

    async def build(self):
        total = await self.qb.total()

        # Current Page
        self.r['current_page'] = self.qp.page

        # Data
        offset = self.qp.size * (self.qp.page - 1)
        self.qb.stmt = self.qb.stmt.offset(offset).limit(self.qp.size)
        self.r['data'] = await self.qb.get()

        # Total
        self.r['total'] = total

        # Per Page
        self.r['per_page'] = self.qp.size

        # Total Page
        self.r['total_pages'] = math.ceil(total / self.qp.size)

    async def get(self) -> dict:
        await self.build()
        return self.r
