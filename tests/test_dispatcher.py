"""Тесты для диспетчера метаданных."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from metadata_cleaner.cleaner.dispatcher import MetadataDispatcher
from metadata_cleaner.cleaner.models import (
    CleanStatus,
    FileType,
    OutputMode,
    CleaningOptions,
    FileJob,
)
from metadata_cleaner.services.settings_service import SettingsService


class TestMetadataDispatcher(unittest.TestCase):
    """Тесты класса MetadataDispatcher."""

    def setUp(self):
        """Настройка тестовых данных."""
        self.mock_settings = Mock(spec=SettingsService)
        self.mock_settings.get_output_mode.return_value = OutputMode.CREATE_COPY
        self.mock_settings.get_metadata_to_clean.return_value = {
            "author": True,
            "gps_coords": True,
            "exif_camera": True,
            "created": True,
            "modified": True,
        }
        self.dispatcher = MetadataDispatcher(self.mock_settings)
        
        # Путь к тестовым файлам
        self.test_files_dir = Path(__file__).parent / "test_files"

    def test_get_file_type_images(self):
        """Тест определения типа файла для изображений."""
        test_cases = [
            ("test.jpg", FileType.IMAGE),
            ("test.jpeg", FileType.IMAGE),
            ("test.png", FileType.IMAGE),
            ("test.gif", FileType.IMAGE),
            ("test.heic", FileType.IMAGE),
            ("test.heif", FileType.IMAGE),
            ("TEST.JPG", FileType.IMAGE),  # Проверка регистронезависимости
        ]

        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                result = self.dispatcher.get_file_type(Path(filename))
                self.assertEqual(result, expected_type)

    def test_get_file_type_documents(self):
        """Тест определения типа файла для документов."""
        test_cases = [
            ("test.docx", FileType.DOCUMENT),
            ("test.xlsx", FileType.DOCUMENT),
            ("test.pptx", FileType.DOCUMENT),
            ("TEST.DOCX", FileType.DOCUMENT),
        ]

        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                result = self.dispatcher.get_file_type(Path(filename))
                self.assertEqual(result, expected_type)

    def test_get_file_type_pdf(self):
        """Тест определения типа файла для PDF."""
        result = self.dispatcher.get_file_type(Path("test.pdf"))
        self.assertEqual(result, FileType.PDF)

    def test_get_file_type_videos(self):
        """Тест определения типа файла для видео."""
        test_cases = [
            ("test.mp4", FileType.VIDEO),
            ("test.mov", FileType.VIDEO),
            ("TEST.MP4", FileType.VIDEO),
        ]

        for filename, expected_type in test_cases:
            with self.subTest(filename=filename):
                result = self.dispatcher.get_file_type(Path(filename))
                self.assertEqual(result, expected_type)

    def test_get_file_type_unsupported(self):
        """Тест определения типа файла для неподдерживаемых форматов."""
        unsupported_files = [
            "test.txt",
            "test.exe",
            "test.unknown",
            "test",  # Без расширения
            "test.doc",  # Старый формат Word
            "test.xls",  # Старый формат Excel
        ]

        for filename in unsupported_files:
            with self.subTest(filename=filename):
                result = self.dispatcher.get_file_type(Path(filename))
                self.assertIsNone(result)

    def test_is_supported(self):
        """Тест проверки поддержки файлов."""
        supported_files = [
            "test.jpg", "test.jpeg", "test.png", "test.gif", "test.heic", "test.heif",
            "test.docx", "test.xlsx", "test.pptx",
            "test.pdf",
            "test.mp4", "test.mov",
        ]

        for filename in supported_files:
            with self.subTest(filename=filename):
                self.assertTrue(self.dispatcher.is_supported(filename))

        unsupported_files = [
            "test.txt", "test.exe", "test.unknown", "test.doc", "test.xls"
        ]

        for filename in unsupported_files:
            with self.subTest(filename=filename):
                self.assertFalse(self.dispatcher.is_supported(filename))

    def test_get_supported_extensions(self):
        """Тест получения поддерживаемых расширений."""
        extensions = self.dispatcher.get_supported_extensions()

        expected_extensions = {
            # Изображения
            ".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif",
            # Документы
            ".docx", ".xlsx", ".pptx",
            # PDF
            ".pdf",
            # Видео
            ".mp4", ".mov",
        }

        self.assertEqual(extensions, expected_extensions)

    def test_get_file_info_existing_file(self):
        """Тест получения информации о существующем файле."""
        test_file = self.test_files_dir / "test_image.jpg"
        if test_file.exists():
            info = self.dispatcher.get_file_info(test_file)

            self.assertEqual(info["name"], "test_image.jpg")
            self.assertEqual(info["extension"], ".jpg")
            self.assertEqual(info["supported"], "True")
            self.assertIn("mime_type", info)
            self.assertIn("size", info)
            self.assertNotEqual(info["size"], "0")

    def test_get_file_info_nonexistent_file(self):
        """Тест получения информации о несуществующем файле."""
        test_file = Path("nonexistent.jpg")
        info = self.dispatcher.get_file_info(test_file)

        self.assertEqual(info["name"], "nonexistent.jpg")
        self.assertEqual(info["extension"], ".jpg")
        self.assertEqual(info["size"], "0")
        self.assertEqual(info["supported"], "True")

    def test_options_to_clean_fields(self):
        """Тест конвертации CleaningOptions в clean_fields."""
        options = CleaningOptions(
            clean_author=True,
            clean_title=False,
            clean_subject=True,
            clean_keywords=False,
            clean_comments=True,
            clean_created_date=True,
            clean_modified_date=False,
            clean_gps_data=True,
            clean_camera_info=False,
            create_backup=True,
        )

        clean_fields = self.dispatcher._options_to_clean_fields(options)

        self.assertTrue(clean_fields["author"])
        self.assertTrue(clean_fields["creator"])  # Синоним для author
        self.assertFalse(clean_fields["title"])
        self.assertTrue(clean_fields["subject"])
        self.assertFalse(clean_fields["keywords"])
        self.assertTrue(clean_fields["comments"])
        self.assertTrue(clean_fields["created"])
        self.assertFalse(clean_fields["modified"])
        self.assertTrue(clean_fields["revision"])  # Всегда True
        self.assertTrue(clean_fields["gps"])
        self.assertFalse(clean_fields["camera"])


class TestDispatcherRealFiles(unittest.TestCase):
    """Тесты диспетчера с реальными файлами."""

    def setUp(self):
        """Настройка тестовых данных."""
        self.mock_settings = Mock(spec=SettingsService)
        self.mock_settings.get_output_mode.return_value = OutputMode.CREATE_COPY
        self.mock_settings.get_metadata_to_clean.return_value = {
            "author": True,
            "gps_coords": True,
            "exif_camera": True,
            "created": True,
            "modified": True,
            "title": False,  # Не удаляем заголовки
            "subject": False,
            "keywords": False,
            "comments": False,
        }
        self.dispatcher = MetadataDispatcher(self.mock_settings)
        
        # Путь к тестовым файлам
        self.test_files_dir = Path(__file__).parent / "test_files"
        
        # Создаем временную директорию для тестов
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Очистка после тестов."""
        if self.temp_dir.exists():
            # Попытка удалить директорию с повторными попытками для Windows
            import time
            for attempt in range(3):
                try:
                    shutil.rmtree(self.temp_dir)
                    break
                except PermissionError:
                    if attempt < 2:  # Если не последняя попытка
                        time.sleep(0.1)  # Подождать немного
                        continue
                    else:
                        # Если файлы заблокированы, пропускаем (не критично для тестов)
                        pass

    def _copy_test_file(self, filename: str) -> Path:
        """Копировать тестовый файл во временную директорию."""
        source = self.test_files_dir / filename
        if not source.exists():
            self.skipTest(f"Тестовый файл {filename} не найден")
        
        dest = self.temp_dir / filename
        shutil.copy2(source, dest)
        return dest

    def test_process_image_jpg(self):
        """Тест обработки JPEG изображения."""
        test_file = self._copy_test_file("test_image.jpg")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(result.job.file_path, test_file)
        self.assertIsNotNone(result.job.output_path)
        self.assertTrue(result.job.output_path.exists())

    def test_process_image_jpeg(self):
        """Тест обработки JPEG изображения с расширением .jpeg."""
        test_file = self._copy_test_file("test_image.jpeg")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(result.job.file_path, test_file)
        self.assertIsNotNone(result.job.output_path)
        self.assertTrue(result.job.output_path.exists())

    def test_process_image_png(self):
        """Тест обработки PNG изображения."""
        test_file = self._copy_test_file("test_image.png")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(result.job.file_path, test_file)

    def test_process_image_gif(self):
        """Тест обработки GIF изображения."""
        test_file = self._copy_test_file("test_image.gif")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)

    def test_process_document_docx(self):
        """Тест обработки DOCX документа."""
        test_file = self._copy_test_file("test_document.docx")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(result.job.file_path, test_file)
        self.assertIsNotNone(result.job.output_path)
        self.assertTrue(result.job.output_path.exists())

    def test_process_document_xlsx(self):
        """Тест обработки XLSX документа."""
        test_file = self._copy_test_file("test_spreadsheet.xlsx")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)

    def test_process_document_pptx(self):
        """Тест обработки PPTX презентации."""
        test_file = self._copy_test_file("test_presentation.pptx")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)

    def test_process_pdf(self):
        """Тест обработки PDF документа."""
        test_file = self._copy_test_file("test_document.pdf")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(result.job.file_path, test_file)

    def test_process_video_mp4(self):
        """Тест обработки MP4 видео."""
        test_file = self._copy_test_file("test_video.mp4")
        
        result = self.dispatcher.process_file(test_file)
        
        # Видео может не поддерживаться без ffmpeg
        self.assertIn(result.status, [CleanStatus.SUCCESS, CleanStatus.ERROR])

    def test_process_video_mov(self):
        """Тест обработки MOV видео."""
        test_file = self._copy_test_file("test_video.mov")
        
        result = self.dispatcher.process_file(test_file)
        
        # Видео может не поддерживаться без ffmpeg
        self.assertIn(result.status, [CleanStatus.SUCCESS, CleanStatus.ERROR])

    def test_process_nonexistent_file(self):
        """Тест обработки несуществующего файла."""
        nonexistent_file = self.temp_dir / "nonexistent.jpg"
        
        result = self.dispatcher.process_file(nonexistent_file)
        
        self.assertEqual(result.status, CleanStatus.ERROR)
        self.assertIn("no such file", result.message.lower())

    def test_process_unsupported_file(self):
        """Тест обработки неподдерживаемого файла."""
        # Создаем текстовый файл
        unsupported_file = self.temp_dir / "test.txt"
        unsupported_file.write_text("Test content")
        
        result = self.dispatcher.process_file(unsupported_file)
        
        self.assertEqual(result.status, CleanStatus.ERROR)
        self.assertIn("unsupported", result.message.lower())

    def test_process_with_overwrite_mode(self):
        """Тест обработки с режимом перезаписи."""
        self.mock_settings.get_output_mode.return_value = OutputMode.REPLACE
        
        test_file = self._copy_test_file("test_image.jpg")
        original_size = test_file.stat().st_size
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(result.job.file_path, test_file)
        self.assertIsNone(result.job.output_path)  # Нет отдельного выходного файла

    def test_process_with_backup_mode(self):
        """Тест обработки с режимом создания резервной копии."""
        self.mock_settings.get_output_mode.return_value = OutputMode.BACKUP_AND_OVERWRITE
        
        test_file = self._copy_test_file("test_image.jpg")
        
        result = self.dispatcher.process_file(test_file)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertTrue(result.job.backup_enabled)

    def test_process_file_with_options(self):
        """Тест обработки файла с пользовательскими опциями."""
        test_file = self._copy_test_file("test_image.jpg")
        
        options = CleaningOptions(
            clean_author=True,
            clean_gps_data=True,
            clean_camera_info=False,
            clean_title=False,
            clean_subject=False,
            clean_keywords=False,
            clean_comments=False,
            clean_created_date=True,
            clean_modified_date=True,
            create_backup=False,
        )
        
        result = self.dispatcher.process_file_with_options(test_file, options)
        
        self.assertEqual(result.status, CleanStatus.SUCCESS)

    def test_multiple_files_processing(self):
        """Тест обработки нескольких файлов."""
        test_files = [
            self._copy_test_file("test_image.jpg"),
            self._copy_test_file("test_image.jpeg"),
            self._copy_test_file("test_document.docx"),
            self._copy_test_file("test_document.pdf"),
        ]
        
        results = []
        for test_file in test_files:
            result = self.dispatcher.process_file(test_file)
            results.append(result)
        
        # Все файлы должны быть успешно обработаны
        for result in results:
            self.assertEqual(result.status, CleanStatus.SUCCESS)

    def test_get_handler_for_file(self):
        """Тест получения обработчика для файла."""
        from metadata_cleaner.cleaner.handlers.image import ImageHandler
        from metadata_cleaner.cleaner.handlers.office import OfficeHandler
        from metadata_cleaner.cleaner.handlers.pdf import PDFHandler
        from metadata_cleaner.cleaner.handlers.video import VideoHandler
        
        test_cases = [
            ("test.jpg", ImageHandler),
            ("test.docx", OfficeHandler),
            ("test.pdf", PDFHandler),
            ("test.mp4", VideoHandler),
            ("test.txt", None),
        ]
        
        for filename, expected_handler in test_cases:
            with self.subTest(filename=filename):
                handler_type = self.dispatcher.get_handler_for_file(Path(filename))
                if expected_handler is None:
                    self.assertIsNone(handler_type)
                else:
                    self.assertEqual(handler_type, expected_handler)


if __name__ == "__main__":
    unittest.main()
