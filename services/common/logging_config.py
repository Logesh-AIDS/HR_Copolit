# services/common/logging_config.py
import json
import logging
import sys
import time
from typing import Any, Dict
from services.common.config import settings

class JSONFormatter(logging.Formatter):
    """
    Structured logging JSON formatter for production environments.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }
        
        # Add exception details if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields if passed via logging methods, e.g. logger.info("...", extra={"key": "val"})
        if hasattr(record, "__dict__"):
            for key, val in record.__dict__.items():
                if key not in {"args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", 
                               "levelname", "levelno", "lineno", "module", "msecs", "msg", "name", 
                               "pathname", "process", "processName", "relativeCreated", "stack_info", "thread", "threadName"}:
                    log_data[key] = val
                    
        return json.dumps(log_data)


def configure_logging():
    """
    Initializes root loggers and overlays default uvicorn/fastapi loggers.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Standard output stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    
    if settings.ENV == "production":
        formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ")
    else:
        # Development mode: readable color-coded format
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    
    # Restructure third-party logging engines to align under root handlers
    for log_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        target_logger = logging.getLogger(log_name)
        target_logger.handlers = []
        target_logger.propagate = True
        
    logging.info(f"Structured logging configured successfully. Mode: {settings.ENV}, Level: {logging.getLevelName(log_level)}")
