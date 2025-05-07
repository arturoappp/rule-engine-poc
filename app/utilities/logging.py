import sys
import threading
from importlib.util import find_spec

import logging
from app.core.config import settings

# Datadog integration
BASE_LOGGING_ATTRS = '%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [function=%(funcName)s] [thread=%(threadName)s]'
DD_ENABLED = bool(getattr(find_spec('ddtrace'), "loader", None))
DD_LOGGING_ATTRS = '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s]'

_LOGGERS_CONTEXT_DATA = {"rule-engine-api": ["entity_type", "rule_name", "category"]}


class ArgsFilter(logging.Filter):
    """
    Filter to clean up the interpolated variables (args) that are passed to the log message with lazy formatting
    """

    def filter(self, record):
        cleaned_args: tuple[str] | dict[str, str] = None
        if isinstance(record.args, tuple):
            cleaned_args = tuple(clean_line_breaks(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            cleaned_args = {key: clean_line_breaks(value) for key, value in record.args.items()}
        record.args = cleaned_args or record.args
        return True


class RELoggerAdapter(logging.LoggerAdapter):
    """
    Adds parameters to the logs and do any required message clean up.
    """

    def __init__(self, base_logger):
        super().__init__(base_logger, {})
        self.params = RELoggerParams()

    def process(self, msg, kwargs):
        valid_params = self.params.get_valid_params()
        kwargs["extra"] = valid_params
        msg = clean_line_breaks(msg)
        return msg, kwargs


class RELoggerParams(threading.local):
    """
    Hold default parameters for the logger. Parameters are local to the current thread so every
    thread should set its own parameters.
    """

    def __init__(self, entity_type=None, rule_name=None, category=None) -> None:
        super().__init__()
        self.set(entity_type, rule_name, category)

    @staticmethod
    def _get_valid(a_dict):
        return {name: value or '' for name, value in a_dict.items()}

    def set(self, entity_type=None, rule_name=None, category=None):
        # Parameters specific for rule engine
        self._params = {
            "entity_type": entity_type,
            "rule_name": rule_name,
            "category": category
        }

    def get_valid_params(self):
        return self._get_valid(self._params)


def init_logging():
    """
    Initialize logging configuration for FastAPI application.
    """
    main_loggers = ["rule-engine-api"]
    loggers = [*main_loggers]

    for logger_name in loggers:
        log = logging.getLogger(logger_name)
        ch = logging.StreamHandler(sys.stdout)

        # Set log level based on environment
        env = settings.ENVIRONMENT
        level = logging.DEBUG if env != "production" else logging.INFO

        context_data = _LOGGERS_CONTEXT_DATA.get(logger_name, None)
        log.handlers.clear()
        log.setLevel(level)
        configure_handler(ch, level, context_data)
        log.addHandler(ch)
        f = ArgsFilter()
        log.addFilter(f)


def configure_handler(handler, level: int, context_data: list[str]) -> None:
    format_elements = [BASE_LOGGING_ATTRS, "- %(message)s"]

    if DD_ENABLED:
        format_elements.insert(1, DD_LOGGING_ATTRS)
    if context_data:
        formatted_context_data = " ".join([f"[{attr}=%({attr})s]" for attr in context_data])
        format_elements.insert(1, formatted_context_data)

    fmt = " ".join(format_elements)
    formatter = logging.Formatter(fmt)
    handler.setLevel(level)
    handler.setFormatter(formatter)


def clean_line_breaks(string: str) -> str:
    return string.replace("\n", "").replace("\r", "").strip() if isinstance(string, str) else string


# Configure the logger
rule_engine_logger = logging.getLogger("rule-engine-api")
logger = RELoggerAdapter(rule_engine_logger)
