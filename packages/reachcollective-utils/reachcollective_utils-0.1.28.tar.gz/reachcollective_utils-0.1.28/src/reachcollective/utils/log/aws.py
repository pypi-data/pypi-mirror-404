import logging
import os
import threading

import structlog


# pylint: disable=attribute-defined-outside-init
class AppAWSLog:
    _instance = None
    _lock = threading.Lock()

    VALID_LOG_LEVELS = {'debug', 'info', 'warning', 'error', 'critical'}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        app_env = os.getenv('APP_ENV', 'local').lower()

        processors = [
            self._filter_unwanted_logs,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]

        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        )

        self._configure_stdout(app_env)
        self.logger = structlog.get_logger()

    @staticmethod
    def _configure_stdout(app_env: str):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))

        logging.basicConfig(
            handlers=[handler],
            level=logging.INFO if app_env != 'local' else logging.DEBUG,
        )

    @staticmethod
    def _filter_unwanted_logs(_, __, event_dict):
        if 'change detected' in str(event_dict.get('event', '')).lower():
            return None
        return event_dict

    def log(self, level: str, message: str, **kwargs):
        lvl = level.lower()
        if lvl not in self.VALID_LOG_LEVELS:
            self.logger.warning(
                'Invalid log level provided',
                provided_level=level,
            )
            lvl = 'info'

        getattr(self.logger, lvl)(message, **kwargs)
