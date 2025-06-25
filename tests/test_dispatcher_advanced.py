"""Расширенные тесты для MetadataDispatcher для улучшения покрытия кода."""

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from metadata_cleaner.cleaner.dispatcher import MetadataDispatcher
from metadata_cleaner.cleaner.errors import FileAccessError, UnsupportedFileTypeError
from metadata_cleaner.cleaner.models import (
    CleaningOptions,
    CleanResult,
    CleanStatus,
    FileJob,
    FileType,
    OutputMode,
)
from metadata_cleaner.services.settings_service import SettingsService


class TestDispatcherAdvanced(unittest.TestCase):
    """Расширенные тесты для MetadataDispatcher."""

    def setUp(self):
        """Настройка перед каждым тестом."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_settings = mock.Mock(spec=SettingsService)
        self.mock_settings.get_output_mode.return_value = OutputMode.CREATE_COPY
        self.mock_settings.get_metadata_to_clean.return_value = {
            "author": True,
            "created": True,
            "gps_coords": True,
        }
        self.dispatcher = MetadataDispatcher(self.mock_settings)

    def tearDown(self):
        """Очистка после каждого теста."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_process_file_with_settings_file_not_exists(self):
        """Тест обработки несуществующего файла."""
        nonexistent_path = self.temp_dir / "nonexistent_file.jpg"
        
        result = self.dispatcher.process_file_with_settings(
            nonexistent_path, FileType.IMAGE
        )
        
        self.assertEqual(result.status, CleanStatus.ERROR)
        self.assertIn("файл не найден", result.message.lower())

    def test_process_file_with_settings_directory_path(self):
        """Тест обработки директории вместо файла."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            
            result = self.dispatcher.process_file_with_settings(
                dir_path, FileType.IMAGE
            )
            
            self.assertEqual(result.status, CleanStatus.ERROR)
            self.assertIn("не является файлом", result.message.lower())

    def test_process_file_with_settings_unsupported_type(self):
        """Тест обработки неподдерживаемого типа файла."""
        with tempfile.NamedTemporaryFile(suffix=".unknown", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"test content")
        
        try:
            # Создаем фейковый FileType который не существует в handlers
            fake_file_type = FileType.IMAGE  # используем валидный FileType
            # но удаляем handler из dispatcher
            del self.dispatcher.handlers[FileType.IMAGE]
            
            result = self.dispatcher.process_file_with_settings(
                tmp_path, fake_file_type
            )
            
            self.assertEqual(result.status, CleanStatus.ERROR)
            self.assertIn("неподдерживаемый тип файла", result.message.lower())
        finally:
            tmp_path.unlink(missing_ok=True)
            # Восстанавливаем handler
            from metadata_cleaner.cleaner.handlers.image import ImageHandler
            self.dispatcher.handlers[FileType.IMAGE] = ImageHandler()

    def test_process_file_with_settings_processing_time(self):
        """Тест отслеживания времени обработки."""
        test_file = self.temp_dir / "test.jpg"
        test_file.write_bytes(b"fake jpg content")
        
        # Создаем мок-обработчик с небольшой задержкой
        mock_handler = mock.Mock()
        def slow_clean(job):
            time.sleep(0.01)  # Небольшая задержка для измеримого времени
            return CleanResult(
                job=job,
                status=CleanStatus.SUCCESS,
                processing_time=0.0  # будет обновлено диспетчером
            )
        mock_handler.clean.side_effect = slow_clean
        self.dispatcher.handlers[FileType.IMAGE] = mock_handler
        
        start_time = time.time()
        result = self.dispatcher.process_file_with_settings(test_file, FileType.IMAGE)
        end_time = time.time()
        
        # Проверяем что время обработки обновилось
        self.assertGreater(result.processing_time, 0)
        self.assertLessEqual(result.processing_time, end_time - start_time + 0.1)  # небольшая погрешность

    def test_get_file_info_comprehensive(self):
        """Всесторонний тест получения информации о файле."""
        # Создаем тестовый файл
        test_file = self.temp_dir / "test_document.pdf"
        test_content = b"PDF test content"
        test_file.write_bytes(test_content)
        
        info = self.dispatcher.get_file_info(test_file)
        
        # Проверяем все поля
        self.assertEqual(info["name"], "test_document.pdf")
        self.assertEqual(info["extension"], ".pdf")
        self.assertEqual(info["size"], str(len(test_content)))
        self.assertEqual(info["supported"], "True")
        self.assertEqual(info["mime_type"], "application/pdf")

    def test_get_file_info_string_path(self):
        """Тест get_file_info со строковым путем."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"fake image")
        
        try:
            info = self.dispatcher.get_file_info(tmp_path)
            
            self.assertTrue(info["name"].endswith(".jpg"))
            self.assertEqual(info["extension"], ".jpg")
            self.assertEqual(info["supported"], "True")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_get_file_info_nonexistent_file(self):
        """Тест get_file_info для несуществующего файла."""
        nonexistent_path = self.temp_dir / "nonexistent.jpg"
        
        info = self.dispatcher.get_file_info(nonexistent_path)
        
        self.assertEqual(info["name"], "nonexistent.jpg")
        self.assertEqual(info["extension"], ".jpg")
        self.assertEqual(info["size"], "0")
        self.assertEqual(info["supported"], "True")

    def test_get_file_info_unknown_mime_type(self):
        """Тест get_file_info для файла с неизвестным MIME-типом."""
        with tempfile.NamedTemporaryFile(suffix=".unknown", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"unknown content")
        
        try:
            info = self.dispatcher.get_file_info(tmp_path)
            
            self.assertEqual(info["mime_type"], "unknown")
            self.assertEqual(info["supported"], "False")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_process_file_with_options_comprehensive(self):
        """Всесторонний тест process_file_with_options."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(b"fake jpeg content")
        
        try:
            options = CleaningOptions(
                clean_author=True,
                clean_title=False,
                clean_subject=True,
                clean_keywords=False,
                clean_comments=True,
                clean_created_date=False,
                clean_modified_date=True,
                clean_gps_data=False,
                clean_camera_info=True,
                create_backup=True,
            )
            
            result = self.dispatcher.process_file_with_options(tmp_path, options)
            
            self.assertIsInstance(result, CleanResult)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_options_to_clean_fields_mapping(self):
        """Тест корректности маппинга _options_to_clean_fields."""
        options = CleaningOptions(
            clean_author=True,
            clean_title=False,
            clean_subject=True,
            clean_keywords=False,
            clean_comments=True,
            clean_created_date=False,
            clean_modified_date=True,
            clean_gps_data=False,
            clean_camera_info=True,
            create_backup=False,
        )
        
        clean_fields = self.dispatcher._options_to_clean_fields(options)
        
        self.assertEqual(clean_fields["author"], True)
        self.assertEqual(clean_fields["creator"], True)  # также мапится на author
        self.assertEqual(clean_fields["title"], False)
        self.assertEqual(clean_fields["subject"], True)
        self.assertEqual(clean_fields["keywords"], False)
        self.assertEqual(clean_fields["comments"], True)
        self.assertEqual(clean_fields["created"], False)
        self.assertEqual(clean_fields["modified"], True)
        self.assertEqual(clean_fields["revision"], True)  # всегда True
        self.assertEqual(clean_fields["gps"], False)
        self.assertEqual(clean_fields["camera"], True)

    def test_process_file_backup_and_overwrite_mode(self):
        """Тест обработки в режиме резервного копирования и перезаписи."""
        test_file = self.temp_dir / "test.jpg"
        test_file.write_bytes(b"fake jpg content")
        
        self.mock_settings.get_output_mode.return_value = OutputMode.BACKUP_AND_OVERWRITE
        
        with mock.patch.object(self.dispatcher.handlers[FileType.IMAGE], 'clean') as mock_clean:
            mock_clean.return_value = CleanResult(
                job=FileJob(file_path=test_file),
                status=CleanStatus.SUCCESS
            )
            
            result = self.dispatcher.process_file(test_file)
            
            # Проверяем что был создан FileJob с backup_enabled=True
            call_args = mock_clean.call_args[0][0]  # первый аргумент первого вызова
            self.assertTrue(call_args.backup_enabled)
            self.assertIsNone(call_args.output_path)

    def test_process_file_replace_mode(self):
        """Тест обработки в режиме замены."""
        test_file = self.temp_dir / "test.pdf"
        test_file.write_bytes(b"fake pdf content")
        
        self.mock_settings.get_output_mode.return_value = OutputMode.REPLACE
        
        with mock.patch.object(self.dispatcher.handlers[FileType.PDF], 'clean') as mock_clean:
            mock_clean.return_value = CleanResult(
                job=FileJob(file_path=test_file),
                status=CleanStatus.SUCCESS
            )
            
            result = self.dispatcher.process_file(test_file)
            
            # Проверяем что был создан FileJob с правильными настройками
            call_args = mock_clean.call_args[0][0]
            self.assertFalse(call_args.backup_enabled)
            self.assertIsNone(call_args.output_path)

    def test_process_file_no_handler_error(self):
        """Тест обработки когда нет доступного обработчика."""
        test_file = self.temp_dir / "test.jpg"
        test_file.write_bytes(b"fake jpg content")
        
        # Удаляем обработчик для IMAGE
        del self.dispatcher.handlers[FileType.IMAGE]
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.ERROR)
        self.assertIn("No handler for file type", result.message)

    def test_get_handler_for_file_all_types(self):
        """Тест получения обработчиков для всех поддерживаемых типов."""
        test_cases = [
            ("test.jpg", "ImageHandler"),
            ("test.jpeg", "ImageHandler"),
            ("test.png", "ImageHandler"),
            ("test.gif", "ImageHandler"),
            ("test.heic", "ImageHandler"),
            ("test.heif", "ImageHandler"),
            ("test.docx", "OfficeHandler"),
            ("test.xlsx", "OfficeHandler"),
            ("test.pptx", "OfficeHandler"),
            ("test.pdf", "PDFHandler"),
            ("test.mp4", "VideoHandler"),
            ("test.mov", "VideoHandler"),
        ]
        
        for filename, expected_handler in test_cases:
            with self.subTest(filename=filename):
                file_path = Path(filename)
                handler_type = self.dispatcher.get_handler_for_file(file_path)
                self.assertIsNotNone(handler_type)
                self.assertEqual(handler_type.__name__, expected_handler)

    def test_get_handler_for_file_unsupported(self):
        """Тест получения обработчика для неподдерживаемого файла."""
        unsupported_files = ["test.txt", "test.exe", "test.unknown", "test"]
        
        for filename in unsupported_files:
            with self.subTest(filename=filename):
                file_path = Path(filename)
                handler_type = self.dispatcher.get_handler_for_file(file_path)
                self.assertIsNone(handler_type)

    def test_is_supported_comprehensive(self):
        """Всесторонний тест проверки поддержки файлов."""
        supported_files = [
            "test.jpg", "test.JPEG", "test.PNG", "test.gif",
            "test.heic", "test.HEIF", "test.docx", "test.XLSX",
            "test.pptx", "test.PDF", "test.mp4", "test.MOV"
        ]
        
        unsupported_files = [
            "test.txt", "test.exe", "test.bat", "test.py",
            "test.js", "test.html", "test.css", "test"
        ]
        
        for filename in supported_files:
            with self.subTest(filename=filename, supported=True):
                self.assertTrue(self.dispatcher.is_supported(filename))
                self.assertTrue(self.dispatcher.is_supported(Path(filename)))
        
        for filename in unsupported_files:
            with self.subTest(filename=filename, supported=False):
                self.assertFalse(self.dispatcher.is_supported(filename))
                self.assertFalse(self.dispatcher.is_supported(Path(filename)))

    def test_get_supported_extensions_complete(self):
        """Тест получения полного списка поддерживаемых расширений."""
        extensions = self.dispatcher.get_supported_extensions()
        
        expected_extensions = {
            # Images
            ".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif",
            # Documents
            ".docx", ".xlsx", ".pptx",
            # PDF
            ".pdf",
            # Video
            ".mp4", ".mov"
        }
        
        self.assertEqual(extensions, expected_extensions)
        self.assertEqual(len(extensions), 12)  # проверяем что всё добавлено

    def test_get_file_type_case_insensitive(self):
        """Тест определения типа файла независимо от регистра."""
        test_cases = [
            ("test.JPG", FileType.IMAGE),
            ("test.JPEG", FileType.IMAGE),
            ("test.PNG", FileType.IMAGE),
            ("test.DOCX", FileType.DOCUMENT),
            ("test.XLSX", FileType.DOCUMENT),
            ("test.PPTX", FileType.DOCUMENT),
            ("test.PDF", FileType.PDF),
            ("test.MP4", FileType.VIDEO),
            ("test.MOV", FileType.VIDEO),
        ]
        
        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                file_path = Path(filename)
                file_type = self.dispatcher.get_file_type(file_path)
                self.assertEqual(file_type, expected_type)


if __name__ == "__main__":
    unittest.main() 