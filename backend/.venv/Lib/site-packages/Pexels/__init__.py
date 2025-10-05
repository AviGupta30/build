"""A unofficial python wrapper library for Pexels API"""

from .client import Client
from .errors import APIError, InvalidTokenError, QuotaExceedError
from .errors import PexelsError, APIError, QuotaExceedError, InvalidTokenError
from .constants import COLOR, ORIENTATION, SIZE, LOCALE_SUPPORTED

__version__ = "1.1"

__author__ = "jokerhacker.6521@protonmail.com"
