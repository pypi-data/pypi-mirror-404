import os
from sqlmodel.ext.asyncio.session import AsyncSession

from .db import AppDBLog


class AppLog:

    @classmethod
    def channel(
        cls,
        channel: str | None = 'default',
        db: AsyncSession | None = None,
        log_model = None,
        instance = None
    ):
        return cls().create_channel(channel, db, log_model, instance)

    @classmethod
    def log(
        cls,
        level,
        message,
        **kwargs
    ):
        return cls().create_channel('default').log(level, message, **kwargs)

    @staticmethod
    def create_channel(
        channel: str,
        db: AsyncSession | None = None,
        log_model = None,
        instance = None
    ):
        if channel == 'db':
            if not db or not log_model:
                raise ValueError('db instance and log_model are required')

            return AppDBLog(db, log_model, instance)

        if channel in {'default'}:
            return AppLog._cloud_logger()

        raise ValueError(f'Invalid option {channel}. Expected db or gcp.')

    @staticmethod
    def _cloud_logger():
        provider = os.getenv('APP_CLOUD_PROVIDER', 'gcp').lower()

        if provider == 'aws':
            from .aws import AppAWSLog
            return AppAWSLog()

        if provider == 'gcp':
            from .gcp import AppGCPLog
            return AppGCPLog()

        raise ValueError(
            f'Invalid APP_CLOUD_PROVIDER "{provider}". Expected "gcp" or "aws".'
        )
