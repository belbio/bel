import logging.config
from structlog import configure, processors, stdlib, threadlocal

# Found in https://blog.sneawo.com/blog/2017/07/28/json-logging-in-python/

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(message)s %(lineno)d %(pathname)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'json': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        }
    },
    'loggers': {
        '': {
            'handlers': ['json'],
            'level': "INFO"
        },
        "bel": {
            "level": "INFO"
        },
        "requests": {
            "level": "DEBUG",
        },
        "elasticsearch": {
            "level": "WARNING"
        },
        "falcon_cors": {
            "level": "WARNING",
            'formatter': 'json',
        },
        "urllib3": {
            "level": "CRITICAL"
        },
        "timy": {
            "level": "ERROR"
        },
    }
})

configure(
    context_class=threadlocal.wrap_dict(dict),
    logger_factory=stdlib.LoggerFactory(),
    wrapper_class=stdlib.BoundLogger,
    processors=[
        stdlib.filter_by_level,
        stdlib.add_logger_name,
        stdlib.add_log_level,
        stdlib.PositionalArgumentsFormatter(),
        processors.TimeStamper(fmt="iso"),
        processors.StackInfoRenderer(),
        processors.format_exc_info,
        processors.UnicodeDecoder(),
        stdlib.render_to_log_kwargs]
)


# import logging
# import logging.config
# import structlog


# def setup_logging():
#     """Setup logging for bel and bel_api"""

#     timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
#     pre_chain = [
#         # Add the log level and a timestamp to the event_dict if the log entry
#         # is not from structlog.
#         structlog.stdlib.add_log_level,
#         timestamper,
#     ]

#     # logging.config.dictConfig(config['logging'])

#     logging.config.dictConfig({
#         "version": 1,
#         "disable_existing_loggers": False,
#         "formatters": {
#             "plain": {
#                 "()": structlog.stdlib.ProcessorFormatter,
#                 "processor": structlog.processors.JSONRenderer(),
#                 "foreign_pre_chain": pre_chain,
#             },
#             # "colored": {
#             #     "()": structlog.stdlib.ProcessorFormatter,
#             #     "processor": structlog.dev.ConsoleRenderer(colors=True),
#             #     "foreign_pre_chain": pre_chain,
#             # },
#         },
#         "handlers": {
#             "default": {
#                 "level": "INFO",
#                 "class": "logging.StreamHandler",
#                 "formatter": "plain",
#             },
#             "colored": {
#                 "level": "DEBUG",
#                 "class": "logging.StreamHandler",
#                 "formatter": "plain",
#             }
#         },
#         "loggers": {
#             "": {
#                 "handlers": ["default"],
#                 "level": "INFO",
#                 "propagate": True,
#             },
#             "elasticsearch": {
#                 "level": "WARNING"
#             },
#             "falcon_cors": {
#                 "level": "DEBUG",
#                 "handlers": ["default"],
#             },
#             "urllib3": {
#                 "level": "CRITICAL"
#             },
#             "timy": {
#                 "level": "ERROR"
#             },
#         }
#     })

#     structlog.configure_once(
#         processors=[
#             structlog.stdlib.filter_by_level,
#             structlog.stdlib.add_logger_name,
#             structlog.stdlib.add_log_level,
#             structlog.stdlib.PositionalArgumentsFormatter(),
#             timestamper,
#             structlog.processors.UnicodeDecoder(),
#             structlog.processors.StackInfoRenderer(),
#             structlog.processors.format_exc_info,
#             structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
#         ],
#         context_class=dict,
#         logger_factory=structlog.stdlib.LoggerFactory(),
#         wrapper_class=structlog.stdlib.BoundLogger,
#         cache_logger_on_first_use=True,
#     )


# import logging.config

# from structlog import configure, processors, stdlib, threadlocal

# logging.config.dictConfig({
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'json': {
#             'format': '%(message)s %(lineno)d %(pathname)s',
#             'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
#         }
#     },
#     'handlers': {
#         'json': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'json'
#         }
#     },
#     'loggers': {
#         '': {
#             'handlers': ['json'],
#             'level': logging.INFO
#         }
#     }
# })

# configure(
#     context_class=threadlocal.wrap_dict(dict),
#     logger_factory=stdlib.LoggerFactory(),
#     wrapper_class=stdlib.BoundLogger,
#     processors=[
#         stdlib.filter_by_level,
#         stdlib.add_logger_name,
#         stdlib.add_log_level,
#         stdlib.PositionalArgumentsFormatter(),
#         processors.TimeStamper(fmt="iso"),
#         processors.StackInfoRenderer(),
#         processors.format_exc_info,
#         processors.UnicodeDecoder(),
#         stdlib.render_to_log_kwargs]
# )
