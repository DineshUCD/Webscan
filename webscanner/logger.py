import os, logging

from .settings import BASE_DIR
from logstash_formatter import LogstashFormatterV1

# The basic logger that other applications can import
# The call to logging.getLogger() obtains (creating, if necessary) an instance of a logger.
logger = logging.getLogger(__name__)

# You also need to configure the loggers, handlers, filters, and formatters.
# Logging dictConfig configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False, # Retain Django's default logger
    'formatters': {
        'logstash': {
            '()': 'logstash_formatter.LogstashFormatter',
            'format': '{"extra":{"app": "app_name"}}',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'standard': { 
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'production_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'main.log'),
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter': 'simple',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        # root configuration - for all the applications
        '': {
            'handlers': ['production_file', 'console'],
            'level': 'DEBUG',
        },
        'django': { # configure all of Django's loggers
            'handlers': ['production_file', 'console'],
            'level': 'INFO',
            'propogate': False,
        },
    },
}

