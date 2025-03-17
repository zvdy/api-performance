"""
Asynchronous Logging Module - Technique #7

This module demonstrates how to implement asynchronous logging to improve API performance
by offloading logging operations to a separate thread or process.
"""

import logging
import threading
import time
import queue
import os
import sys
import json
from typing import Dict, Any, Optional
import asyncio
import structlog

# Create a queue for log messages
log_queue = queue.Queue()

# Flag to control the logging thread
should_stop = threading.Event()

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # 'json' or 'text'

def log_worker():
    """
    Worker function that runs in a separate thread to process log messages from the queue
    """
    logger = logging.getLogger("async_logger")
    
    while not should_stop.is_set() or not log_queue.empty():
        try:
            # Get a log message from the queue with a timeout
            record = log_queue.get(timeout=0.5)
            
            # Process the log message based on level
            level = record.get("level", "info").lower()
            message = record.get("message", "")
            extra = record.get("extra", {})
            
            if level == "debug":
                logger.debug(message, extra=extra)
            elif level == "info":
                logger.info(message, extra=extra)
            elif level == "warning":
                logger.warning(message, extra=extra)
            elif level == "error":
                logger.error(message, extra=extra)
            elif level == "critical":
                logger.critical(message, extra=extra)
            else:
                # Default to info level
                logger.info(message, extra=extra)
                
            # Mark the task as done
            log_queue.task_done()
            
        except queue.Empty:
            # No log messages in the queue, just continue
            continue
        except Exception as e:
            # Log any errors in the logging thread itself
            sys.stderr.write(f"Error in logging thread: {str(e)}\n")
            sys.stderr.flush()

def log_request(message: str, extra: Optional[Dict[str, Any]] = None):
    """
    Asynchronously log a message by adding it to the log queue
    
    Args:
        message: Log message
        extra: Additional log data
    """
    if extra is None:
        extra = {}
    
    # Add timestamp if not provided
    if "timestamp" not in extra:
        extra["timestamp"] = time.time()
    
    # Default to info level if not specified
    level = extra.pop("level", "info")
    
    # Add to the queue
    log_queue.put({
        "message": message,
        "level": level,
        "extra": extra
    })

def setup_async_logging():
    """
    Setup asynchronous logging with structlog
    
    Returns:
        Configured structlog logger
    """
    # Configure logging level
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Configure basic logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Start the logging thread
    logging_thread = threading.Thread(target=log_worker, daemon=True)
    logging_thread.start()
    
    # Get a logger instance
    logger = structlog.get_logger("api")
    
    return logger

def stop_async_logging():
    """
    Stop the async logging thread gracefully
    """
    # Signal the thread to stop
    should_stop.set()
    
    # Wait for the queue to empty
    if not log_queue.empty():
        log_queue.join()  # Wait for all tasks to be processed

class AsyncLogHandler(logging.Handler):
    """
    Custom logging handler that sends logs to the async queue
    """
    def emit(self, record):
        try:
            # Format the record
            message = self.format(record)
            
            # Extract level
            level = record.levelname.lower()
            
            # Add to queue
            log_queue.put({
                "message": message,
                "level": level,
                "extra": {
                    "logger": record.name,
                    "path": record.pathname,
                    "lineno": record.lineno,
                    "timestamp": time.time()
                }
            })
        except Exception:
            self.handleError(record) 