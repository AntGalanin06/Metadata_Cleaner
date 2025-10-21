"""Handlers for metadata cleaning."""

from metadata_cleaner_core.engine.handlers.base import BaseHandler
from metadata_cleaner_core.engine.handlers.image import ImageHandler
from metadata_cleaner_core.engine.handlers.office import OfficeHandler
from metadata_cleaner_core.engine.handlers.pdf import PDFHandler
from metadata_cleaner_core.engine.handlers.video import VideoHandler

__all__ = [
    "BaseHandler",
    "ImageHandler",
    "OfficeHandler",
    "PDFHandler",
    "VideoHandler",
]
