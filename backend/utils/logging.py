"""Centralized logging configuration for Tiger ID.

Handles log rotation safely on Windows (where file locking prevents
the standard RotatingFileHandler from renaming open files) and ensures
that file-handler failures never silence console output.
"""

import structlog
import logging
import sys
import os
import platform
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


# ---------------------------------------------------------------------------
# Windows-safe rotating file handler
# ---------------------------------------------------------------------------

class SafeRotatingFileHandler(RotatingFileHandler):
    """A RotatingFileHandler that does not crash on rotation errors.

    On Windows the standard handler calls ``os.rename`` / ``os.remove``
    which fail with ``PermissionError`` when any process (or even the
    same process) holds an open handle on the log file.  When that
    happens the ``emit`` call raises and Python's logging machinery
    marks the handler as broken, silently swallowing **all** subsequent
    log records -- including those destined for other handlers on the
    same logger.

    This subclass catches rotation errors and falls back gracefully:
    * The current log message is still written (to the existing file,
      even if it exceeds ``maxBytes``).
    * A warning is printed to stderr so the developer knows rotation
      failed.
    * On the **next** emit the handler will try to rotate again.

    On Windows we also use ``delay=True`` so the file is not kept open
    between writes, reducing the window for lock conflicts.
    """

    def __init__(self, *args, **kwargs):
        # On Windows, use delay mode to avoid keeping file handles open
        if platform.system() == "Windows":
            kwargs.setdefault("delay", True)
        super().__init__(*args, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record, catching rotation failures."""
        try:
            super().emit(record)
        except (OSError, PermissionError) as exc:
            # Rotation failed (most likely Windows file-lock).
            # Try writing without rotation as a fallback so the log
            # message is not lost.
            try:
                # Temporarily disable rotation by raising the threshold
                original_max = self.maxBytes
                self.maxBytes = 0  # 0 = no rotation
                try:
                    super().emit(record)
                finally:
                    self.maxBytes = original_max
            except Exception:
                # Absolute last resort -- at least don't crash
                pass
            # Notify on stderr (never silently swallow)
            try:
                sys.stderr.write(
                    f"[logging] RotatingFileHandler rotation failed "
                    f"for {self.baseFilename}: {exc}\n"
                )
            except Exception:
                pass

    def doRollover(self) -> None:
        """Perform rollover with Windows-safe error handling."""
        try:
            super().doRollover()
        except (OSError, PermissionError) as exc:
            # On Windows, if rotation fails due to file locking,
            # truncate the current file instead of leaving it bloated.
            try:
                if self.stream:
                    self.stream.close()
                    self.stream = None  # type: ignore[assignment]
                # Try to truncate the file so logging can continue
                with open(self.baseFilename, "w", encoding=self.encoding or "utf-8"):
                    pass  # truncate
                # Re-open the stream
                self.stream = self._open()
                sys.stderr.write(
                    f"[logging] Rotation failed, truncated {self.baseFilename}: {exc}\n"
                )
            except Exception as inner_exc:
                sys.stderr.write(
                    f"[logging] Rotation AND truncation failed "
                    f"for {self.baseFilename}: {exc} / {inner_exc}\n"
                )
                # Re-open stream so future writes don't crash
                try:
                    self.stream = self._open()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_file_handlers() -> list[logging.Handler]:
    """Create file handlers, returning an empty list if anything goes wrong.

    This guarantees that a missing directory, permission error, or any
    other OS-level issue does **not** prevent the application from
    starting and logging to the console.
    """
    handlers: list[logging.Handler] = []
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "app.log"
        error_log_file = log_dir / "error.log"

        fmt = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        app_handler = SafeRotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(fmt)
        handlers.append(app_handler)

        error_handler = SafeRotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        handlers.append(error_handler)

    except Exception as exc:
        # File logging is non-critical -- warn but do not crash.
        sys.stderr.write(
            f"[logging] Could not set up file logging: {exc}\n"
        )

    return handlers


def _setup_console_handler() -> logging.Handler:
    """Create a console (stdout) handler.  This must never fail."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    return handler


# Build handlers
_console_handler = _setup_console_handler()
_file_handlers = _setup_file_handlers()

# ---------------------------------------------------------------------------
# Configure the "backend" namespace logger instead of the root logger.
#
# Previously we configured the root logger which interfered with uvicorn's
# own loggers (uvicorn, uvicorn.access, uvicorn.error).  Uvicorn's default
# LOGGING_CONFIG uses ``disable_existing_loggers: True`` in dictConfig,
# which silences any loggers already created before uvicorn runs its own
# config.  Even when that flag is False, adding handlers on root caused
# duplicate or missing output because uvicorn's access logger sets
# ``propagate: False`` by default.
#
# By scoping our handlers to the "backend" namespace logger:
#   1. All application loggers (backend.api.*, backend.services.*, etc.)
#      propagate up to "backend" and hit our console + file handlers.
#   2. Uvicorn's loggers remain completely untouched so access-log lines
#      like ``INFO: 127.0.0.1 - "GET /..." 200`` appear as expected.
#   3. File rotation and structlog integration continue to work unchanged.
# ---------------------------------------------------------------------------
_app_logger = logging.getLogger("backend")
_app_logger.setLevel(logging.DEBUG)
_app_logger.propagate = False  # Don't bubble up to root; we handle it here
_app_logger.addHandler(_console_handler)
for _fh in _file_handlers:
    _app_logger.addHandler(_fh)

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
        # Use ConsoleRenderer for terminals, JSON for non-tty (production)
        structlog.dev.ConsoleRenderer()
        if sys.stderr.isatty()
        else structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a configured structlog logger instance.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A bound structlog logger that writes to console (always) and
        to rotating log files (when available).
    """
    return structlog.get_logger(name)
