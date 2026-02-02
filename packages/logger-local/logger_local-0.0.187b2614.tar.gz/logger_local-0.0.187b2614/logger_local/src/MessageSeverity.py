from enum import Enum


# TODO Capitalize the severity names in the enum
class MessageSeverity(Enum):
    DEBUG = 100
    VERBOSE = 200
    INIT = 300
    START = 400
    END = 402
    INFORMATION = 500
    WARNING = 600
    ERROR = 700
    CRITICAL = 800
    EXCEPTION = 900
