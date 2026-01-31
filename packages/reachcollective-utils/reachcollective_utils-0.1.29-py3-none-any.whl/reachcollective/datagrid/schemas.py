from fastapi import Query, Request
from pydantic import BaseModel, PrivateAttr


class DataGridQueryParams(BaseModel):
    sort: str | None = Query(None)
    include: str | None = Query(None)
    view: str | None = Query(None)
    size: int | None = Query(None)
    page: int | None = Query(None)
    _request: Request = PrivateAttr()

    @classmethod
    def from_request(cls, request: Request) -> 'DataGridQueryParams':
        query = request.query_params
        instance = cls(
            sort=query.get('sort'),
            include=query.get('include'),
            view=query.get('view'),
            size=int(query.get('size')) if query.get('size') else None,
            page=int(query.get('page')) if query.get('page') else None,
        )

        instance._request = request
        return instance

    @property
    def request(self) -> Request:
        if self._request is None:
            raise RuntimeError('Request not initialized')
        return self._request
