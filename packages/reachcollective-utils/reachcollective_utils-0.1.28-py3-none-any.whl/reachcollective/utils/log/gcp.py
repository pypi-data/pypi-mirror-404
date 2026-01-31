import logging
import os
import threading

import structlog
from google.cloud import logging as cloud_logging
from structlog.exceptions import DropEvent  # <- needed to drop the event cleanly


# pylint: disable=attribute-defined-outside-init
class AppGCPLog:
    _instance = None
    _lock = threading.Lock()

    VALID_LOG_LEVELS = {'debug', 'info', 'warning', 'error', 'critical'}

    def __new__(cls):
        # Singleton initialization
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Resolve environment
        app_env = os.getenv('APP_ENV', 'local').lower()

        # Base processors applied in all environments
        base_processors = [
            self._filter_unwanted_logs,                      # Drop noisy/unwanted events
            structlog.processors.TimeStamper(fmt='iso'),     # Add ISO timestamp
            structlog.processors.add_log_level,              # Ensure 'level' exists in event_dict
        ]

        if app_env == 'local':
            # In local, render JSON to stdout for easy dev viewing
            processors = [
                *base_processors,
                structlog.stdlib.filter_by_level,            # Honor stdlib log level
                structlog.processors.JSONRenderer(),         # Print JSON to stdout
            ]
            self._configure_console()
        else:
            # In non-local, send to Cloud Logging and DROP the record to avoid stdout duplicates
            processors = [
                *base_processors,
                self._google_cloud_processor(),              # Send to Cloud Logging (then DropEvent)
            ]
            self._configure_google_cloud()

        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        )
        self.logger = structlog.get_logger()

    def _configure_google_cloud(self):
        # Create Cloud Logging client and named logger
        self.cloud_client = cloud_logging.Client()
        self.cloud_logger = self.cloud_client.logger('payswell-api')

    def _google_cloud_processor(self):
        # Processor that sends the event dict to Cloud Logging with proper severity
        def processor(_, method_name, event_dict):
            # Prefer explicit 'level'; fallback to structlog 'method_name'
            level = (event_dict.pop('level', None) or method_name or 'info').lower()
            severity = self._get_severity(level)

            # Send structured payload to Cloud Logging
            self.cloud_logger.log_struct(event_dict, severity=severity)

            # IMPORTANT: Raising DropEvent tells structlog to stop processing without error.
            # This avoids the "last processor must return ..." ValueError and prevents stdout logs.
            raise DropEvent
        return processor

    @staticmethod
    def _configure_console():
        # Configure basic stdout handler for local development
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logging.basicConfig(handlers=[handler], level=logging.INFO)

    @staticmethod
    def _get_severity(level: str) -> str:
        # Map structlog/stdlib level to Cloud Logging severity
        return {
            'debug': 'DEBUG',
            'info': 'INFO',
            'warning': 'WARNING',
            'error': 'ERROR',
            'critical': 'CRITICAL',
        }.get(level, 'DEFAULT')

    @staticmethod
    def _filter_unwanted_logs(_, __, event_dict):
        # Drop events matching unwanted patterns (case-insensitive)
        if 'change detected' in str(event_dict.get('event', '')).lower():
            return None
        return event_dict

    def log(self, level: str, message: str, **kwargs):
        # Public logging API with validation
        lvl = level.lower()
        if lvl not in self.VALID_LOG_LEVELS:
            self.logger.warning(f'Invalid log level "{level}" provided. Defaulting to "info".')
            lvl = 'info'
        getattr(self.logger, lvl)(message, **kwargs)
