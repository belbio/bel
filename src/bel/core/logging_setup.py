# Local Imports
# Standard Library
import sys

# Third Party
from loguru import logger

logger.add(
    sys.stderr,
    serialize=True,
    colorize=True,
    format="{time} {level} {file} {line} <c>{message}</c>",
    filter="my_module",
    level="INFO",
)


# # Standard Library
# # from loguru import logger
# import datetime
# from loguru import logger
# import sys

# # Third Party Imports
# from loguru import logger
# from loguru import logger._frames
# from
#  import jsonlogger

# # Local Imports
# import bel.core.settings as settings

# """Notes

# Example on how to setup gunicorn well: http://stevetarver.github.io/2017/05/10/python-falcon-logging.html

# """

# JSON_INDENT = 4


# class CustomJsonFormatter(jsonlogger.JsonFormatter):
#     """Customize python json logger to match structlog"""

#     def add_fields(self, log_record, record, message_dict):
#         super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
#         if not log_record.get("timestamp"):
#             # this doesn't use record.created, so it is slightly off
#             now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
#             log_record["timestamp"] = now
#         if log_record.get("level"):
#             log_record["level"] = log_record["level"].upper()
#         else:
#             log_record["level"] = record.levelname


# def add_structlog_app_context(logger, method_name, event_dict):
#     f, name = structlog._frames._find_first_app_frame_and_name(["logging", __name__])
#     event_dict["file"] = f.f_code.co_filename
#     event_dict["line"] = f.f_lineno
#     event_dict["function"] = f.f_code.co_name

#     return event_dict


# # Configure Stdlib logging
# formatter = CustomJsonFormatter("(timestamp) (level) (name) (message)", json_indent=JSON_INDENT)
# handler = logging.StreamHandler(sys.stdout)
# handler.setFormatter(formatter)

# root_logger = logging.getLogger()
# root_logger.addHandler(handler)
# root_logger.setLevel(settings.LOG_LEVEL)

# bel_logger = logging.getLogger("bel")
# bel_logger.addHandler(handler)
# bel_logger.setLevel(settings.LOG_LEVEL)

# belapi_logger = logging.getLogger("belapi")
# belapi_logger.addHandler(handler)
# belapi_logger.setLevel(settings.LOG_LEVEL)

# # Turn off uvicorn access logging by default
# uvicorn_logger = logging.getLogger("uvicorn")
# uvicorn_logger.setLevel("WARNING")

# uvicornerror_logger = logging.getLogger("uvicorn.error")
# uvicornerror_logger.setLevel("WARNING")

# uvicornasgi_logger = logging.getLogger("uvicorn.asgi")
# uvicornasgi_logger.setLevel("WARNING")

# uvicornaccess_logger = logging.getLogger("uvicorn.access")
# uvicornaccess_logger.setLevel("WARNING")

# elasticsearch_logger = logging.getLogger("elasticsearch")
# elasticsearch_logger.setLevel("WARNING")

# urllib3_logger = logging.getLogger("urllib3")
# urllib3_logger.setLevel("WARNING")

# httpx_logger = logging.getLogger("httpx")
# httpx_logger.setLevel("WARNING")

# fastapi_logger = logging.getLogger("fastapi")
# fastapi_logger.setLevel("WARNING")

# websockets_logger = logging.getLogger("websockets")
# websockets_logger.setLevel("WARNING")

# structlog.configure(
#     processors=[
#         structlog.stdlib.filter_by_level,
#         structlog.stdlib.add_logger_name,
#         structlog.stdlib.add_log_level,
#         structlog.processors.StackInfoRenderer(),
#         structlog.dev.set_exc_info,
#         add_structlog_app_context,
#         structlog.processors.format_exc_info,
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.stdlib.render_to_log_kwargs,
#     ],
#     wrapper_class=structlog.stdlib.BoundLogger,
#     context_class=dict,  # or OrderedDict if the runtime's dict is unordered (e.g. Python <3.6)
#     logger_factory=structlog.stdlib.LoggerFactory(),
#     cache_logger_on_first_use=True,
# )
