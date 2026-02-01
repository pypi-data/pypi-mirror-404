"""Lightweight logger helper used across Quantify."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return the named logger without attaching local handlers.

    Central application startup code configures the root/quantify logger with
    `FileHandler`, formatting, log-level, etc.  Attaching an extra
    ``StreamHandler`` here caused messages from modules that invoked this
    helper to bypass that global configuration and go straight to stdout
    (see issue #N/A).  By returning the bare logger, we allow messages to
    propagate and be processed consistently by the existing handlers.
    """

    return logging.getLogger(name)
