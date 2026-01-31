import uuid

from fastapi import HTTPException
from fastapi import status as http_status
from sqlmodel.ext.asyncio.session import AsyncSession


class BaseService:
    # Must be set in subclasses: a repository CLASS (e.g., OfferRepository)
    model_repository = None

    def __init__(self, db: AsyncSession):
        if type(self).model_repository is None:
            raise RuntimeError(f'{type(self).__name__}.model_repository must be set to a repository class')
        self.db = db
        self.auth = None
        self.repository = type(self).model_repository(db)  # pylint: disable=not-callable

        # (optional) sanity checks:
        if not hasattr(self.repository, 'find'):
            raise TypeError('repository must implement .find(id_)')
        if not hasattr(self.repository, 'model'):
            raise TypeError('repository must expose .model (the model class)')

    @property
    def entity_name(self) -> str:
        model = getattr(self.repository, 'model', None)
        return getattr(model, '__name__', 'Resource')

    async def get_or_404(self, id_: uuid.UUID, include: list | None = None):
        entity = await self.repository.find(id_, include)
        if entity is None:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND,f'{self.entity_name} with ID {id_} not found.')
        return entity
