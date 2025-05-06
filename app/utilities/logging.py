import http

from fastapi import requests

import logging
import os
import sys
import threading
from importlib.util import find_spec



INFLUXDB_URL = os.environ["INFLUXDB_URL"]

BASE_LOGGING_ATTRS = '%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [function=%(funcName)s] [thread=%(threadName)s]'
DD_ENABLED = bool(getattr(find_spec('ddtrace'), "loader", None))
DD_LOGGING_ATTRS = '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s]'

_LOGGERS_CONTEXT_DATA = {"rule-engine-api": ["ritm", "sctask", "device"]}


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


class NDCLoggerAdapter(logging.LoggerAdapter):
    """
    Adds parameters to the logs and do any required message clean up.
    """

    def __init__(self, base_logger):
        super().__init__(base_logger, {})
        self.params = NDCLoggerParams()

    def process(self, msg, kwargs):
        valid_params = self.params.get_valid_params()
        kwargs["extra"] = valid_params
        msg = clean_line_breaks(msg)
        return msg, kwargs


class NDCLoggerParams(threading.local):
    """
    Hold default parameters for the logger. Parameters are local to the current thread so every
    thread should set its own parameters. The dimensions property holds parameters that should
    be added to the custom_dimensions in AppInsights but not to the log messages.
    """

    def __init__(self, ritm=None, task=None, device=None) -> None:
        super().__init__()
        self.set(ritm, task)

    @staticmethod
    def _get_valid(a_dict):
        return {name: value or '' for name, value in a_dict.items()}

    def set(self, ritm=None, task=None, device=None):
        self._params = {
            "ritm": ritm,
            "sctask": task,
            "device": device
        }

    def get_valid_params(self):
        return self._get_valid(self._params)


class InfluxHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        # send_to_influx('ndc_log', log_entry.strip(), {'level': record.levelname})


def send_to_influx(measurement, value, keys=None):
    try:
        data_to_write = f'{measurement}'
        if keys:
            keys = ['{}={}'.format(key, item.replace(" ", "\\ ")) if isinstance(item, str) else '{}={}'.format(key, item) for key, item in keys.items()]
            data_to_write += f",{','.join(keys)}"
        data_to_write += ' value="{}"'.format(value.replace("\"", r"\"")) if isinstance(value, str) else ' value="{}"'.format(value)
        resp = requests.post(INFLUXDB_URL + 'write?db=ndc', data=data_to_write.encode(), verify=False, timeout=10)
        if resp.status_code != http.HTTPStatus.NO_CONTENT:
            raise Exception
    except Exception as _:
        logger.debug(f'Could not send data to influxdb. {value}')


def init_logging(flask_app):
    """
    Init all logging configuration.
    """

    main_loggers = ["ndc-api", "emsnow", "werkzeug"]
    tasks_loggers = [t for t in os.listdir(os.path.realpath("app/tasks")) if not t.startswith("__") and os.path.isdir(os.path.abspath(f"app/tasks/{t}"))]
    loggers = [*main_loggers, *tasks_loggers]
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        ch = logging.StreamHandler(sys.stdout)
        # We set DEBUG for the NDC logger and for tasks loggers if app is running in production
        level = logging.DEBUG if "ndc" in logger_name or (os.environ["FLASK_ENV"] != "production" and logger_name in tasks_loggers) else logging.INFO

        context_data = _LOGGERS_CONTEXT_DATA.get(logger_name, None)
        logger.handlers.clear()
        logger.setLevel(level)
        configure_handler(ch, level, context_data)
        logger.addHandler(ch)
        f = ArgsFilter()
        logger.addFilter(f)


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


ndc_logger = logging.getLogger("ndc-api")
logger = NDCLoggerAdapter(ndc_logger)
