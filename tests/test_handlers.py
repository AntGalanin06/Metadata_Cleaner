import tempfile
from pathlib import Path

import pytest

from metadata_cleaner.cleaner.handlers import BaseHandler
from metadata_cleaner.cleaner.handlers.image import ImageHandler
from metadata_cleaner.cleaner.handlers.office import OfficeHandler  
from metadata_cleaner.cleaner.handlers.pdf import PDFHandler
from metadata_cleaner.cleaner.handlers.video import VideoHandler
from metadata_cleaner.cleaner.models import CleanResult, CleanStatus, FileJob, FileType


class TestImageHandler:
    """Базовые тесты для ImageHandler."""

    def setup_method(self):
        self.handler = ImageHandler()

    def test_clean_nonexistent_file(self):
        """Тест обработки несуществующего файла."""
        file_path = Path("nonexistent.jpg")
        job = FileJob(file_path=file_path, file_type=FileType.IMAGE)
        
        result = self.handler.clean(job)
        
        assert result.status == CleanStatus.ERROR

    def test_clean_unsupported_image_format(self):
        """Тест обработки неподдерживаемого формата изображения."""
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"fake image data")
        
        try:
            job = FileJob(file_path=tmp_path, file_type=FileType.IMAGE)
            result = self.handler.clean(job)
            
            assert result.status == CleanStatus.ERROR
        finally:
            tmp_path.unlink(missing_ok=True)


class TestOfficeHandler:
    """Базовые тесты для OfficeHandler."""

    def setup_method(self):
        self.handler = OfficeHandler()

    def test_clean_nonexistent_file(self):
        """Тест обработки несуществующего Office файла."""
        file_path = Path("nonexistent.docx")
        job = FileJob(file_path=file_path, file_type=FileType.DOCUMENT)
        
        result = self.handler.clean(job)
        
        assert result.status == CleanStatus.ERROR

    def test_clean_unsupported_office_format(self):
        """Тест обработки неподдерживаемого Office формата."""
        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"fake doc data")
        
        try:
            job = FileJob(file_path=tmp_path, file_type=FileType.DOCUMENT)
            result = self.handler.clean(job)
            
            assert result.status == CleanStatus.ERROR
        finally:
            tmp_path.unlink(missing_ok=True)


class TestPDFHandler:
    """Базовые тесты для PDFHandler."""

    def setup_method(self):
        self.handler = PDFHandler()

    def test_clean_nonexistent_file(self):
        """Тест обработки несуществующего PDF файла."""
        file_path = Path("nonexistent.pdf")
        job = FileJob(file_path=file_path, file_type=FileType.PDF)
        
        result = self.handler.clean(job)
        
        assert result.status == CleanStatus.ERROR


class TestVideoHandler:
    """Базовые тесты для VideoHandler."""

    def setup_method(self):
        self.handler = VideoHandler()

    def test_clean_nonexistent_file(self):
        """Тест обработки несуществующего видео файла."""
        file_path = Path("nonexistent.mp4")
        job = FileJob(file_path=file_path, file_type=FileType.VIDEO)
        
        result = self.handler.clean(job)
        
        assert result.status == CleanStatus.ERROR


class TestHandlersIntegration:
    """Интеграционные тесты для всех обработчиков."""

    def setup_method(self):
        self.handlers = [
            ImageHandler(),
            OfficeHandler(),
            PDFHandler(),
            VideoHandler(),
        ]

    def test_all_handlers_implement_base_interface(self):
        """Проверка, что все обработчики наследуются от BaseHandler."""
        for handler in self.handlers:
            assert isinstance(handler, BaseHandler)
            assert hasattr(handler, 'clean')
            assert callable(getattr(handler, 'clean'))

    def test_backup_creation_consistency(self):
        """Проверка консистентности создания резервных копий."""
        for handler in self.handlers:
            assert hasattr(handler, '_create_backup')
            assert callable(getattr(handler, '_create_backup')) 