from fastapi import Request

from .filters import Filters


class QueryParams:
    def __init__(self, request: Request, qp=None):
        self.qp = qp.copy() if qp else None
        self.filters = Filters(self.qp)
        self.sort = []
        self.include = []
        self.view = 'list'
        self.request = request
        self.page = 1
        self.size = 15
        self.r = {}

    def process_sort(self) -> None:
        if 'sort' in self.qp:
            direction = 'asc'
            col = self.qp['sort']
            if self.qp['sort'].find('-', 0, 1) >= 0:
                direction = 'desc'
                col = self.qp['sort'][1:]

            self.sort = [{'col': col, 'dir': direction, 'by': self.qp['sort']}]

    def process_include(self):
        parts = []
        if 'include' in self.qp:
            parts = self.qp['include'].split(',')
            for idx, x in enumerate(parts):
                parts[idx] = x.strip()

        if self.include:
            parts = list(set(self.include + parts))

        self.include = parts

    def process(self) -> None:
        self.process_sort()
        self.process_include()

        if 'page' in self.qp:
            self.page = int(self.qp['page'])

        if 'size' in self.qp:
            self.size = int(self.qp['size'])

        if 'view' in self.qp:
            self.view = self.qp['view']

    def get(self):
        self.qp = dict(self.request.query_params)
        self.filters.qp = dict(self.request.query_params)

        # Filters
        self.process()
        self.filters.process()
        filters = self.filters.get()
        if any(filters):
            self.r['filters'] = filters

        self.r['include'] = self.include
        self.r['sort'] = self.sort
        self.r['view'] = self.view
        self.r['page'] = self.page
        self.r['size'] = self.size

        return self.r
