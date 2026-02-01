def default_config(log_level="INFO", rotation_backup_count=5):
    return {
        "version": 1,
        "formatters": {
            "simple_file": {
                "format": "%(asctime)s - %(levelname)s - %(processName)s.%(process)d - %(threadName)s.%(thread)d - %(module)s.%(funcName)s.%(lineno)d - %(message)s"
            }
        },
        "handlers": {
            "logfile_ALL": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "DEBUG",
                "formatter": "simple_file",
                "filename": "",
                "when": "D",
                "interval": 1,
                "encoding": "utf8",
                "backupCount": rotation_backup_count
            },
            "logfile_ERR": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "ERROR",
                "formatter": "simple_file",
                "filename": "",
                "when": "D",
                "interval": 1,
                "encoding": "utf8",
                "backupCount": rotation_backup_count
            }
        },
        "loggers": {
            "defaultLogger": {
                "level": log_level,
                "handlers": [
                    "logfile_ALL",
                    "logfile_ERR"
                ],
                "propagate": "no"
            }
        },
        "root": {
            "level": log_level,
            "handlers": [
                "logfile_ALL",
                "logfile_ERR"
            ]
        }
    }
