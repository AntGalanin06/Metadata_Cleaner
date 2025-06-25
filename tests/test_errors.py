"""Тесты для пользовательских исключений."""

import unittest
from pathlib import Path

from metadata_cleaner.cleaner.errors import (
    MetadataCleanerError,
    FileAccessError,
    UnsupportedFileTypeError,
    MetadataProcessingError,
    BackupError,
    CorruptedFileError,
    EncryptedFileError,
)


class TestMetadataCleanerError(unittest.TestCase):
    """Тесты для базового исключения MetadataCleanerError."""

    def test_basic_creation(self):
        """Тест создания базового исключения."""
        error = MetadataCleanerError("Test error message")
        
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, Exception)

    def test_empty_message(self):
        """Тест создания исключения с пустым сообщением."""
        error = MetadataCleanerError("")
        
        self.assertEqual(str(error), "")

    def test_unicode_message(self):
        """Тест создания исключения с Unicode сообщением."""
        unicode_message = "Ошибка обработки файла 测试 🔒"
        error = MetadataCleanerError(unicode_message)
        
        self.assertEqual(str(error), unicode_message)

    def test_inheritance(self):
        """Тест наследования от Exception."""
        error = MetadataCleanerError("test")
        
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, MetadataCleanerError)


class TestFileAccessError(unittest.TestCase):
    """Тесты для FileAccessError."""

    def test_creation_with_file_path(self):
        """Тест создания ошибки с путем к файлу."""
        file_path = Path("test_file.jpg")
        error = FileAccessError(f"Cannot access file: {file_path}")
        
        self.assertIn("test_file.jpg", str(error))
        self.assertIsInstance(error, MetadataCleanerError)

    def test_file_not_found_scenario(self):
        """Тест сценария отсутствия файла."""
        file_path = Path("nonexistent.jpg")
        error = FileAccessError(f"File not found: {file_path}")
        
        self.assertIn("File not found", str(error))
        self.assertIn("nonexistent.jpg", str(error))

    def test_permission_denied_scenario(self):
        """Тест сценария отказа в доступе."""
        file_path = Path("/protected/file.jpg")
        error = FileAccessError(f"Permission denied: {file_path}")
        
        self.assertIn("Permission denied", str(error))
        # Используем str(file_path) для кроссплатформенности
        self.assertIn(str(file_path), str(error))

    def test_inheritance(self):
        """Тест наследования."""
        error = FileAccessError("test")
        
        self.assertIsInstance(error, MetadataCleanerError)
        self.assertIsInstance(error, Exception)


class TestUnsupportedFileTypeError(unittest.TestCase):
    """Тесты для UnsupportedFileTypeError."""

    def test_creation_with_file_extension(self):
        """Тест создания ошибки с расширением файла."""
        extension = ".txt"
        error = UnsupportedFileTypeError(f"Unsupported file type: {extension}")
        
        self.assertIn(".txt", str(error))
        self.assertIsInstance(error, MetadataCleanerError)

    def test_unknown_extension_scenario(self):
        """Тест сценария неизвестного расширения."""
        file_path = Path("file.unknown")
        error = UnsupportedFileTypeError(f"Unknown file extension: {file_path.suffix}")
        
        self.assertIn("Unknown file extension", str(error))
        self.assertIn(".unknown", str(error))

    def test_inheritance(self):
        """Тест наследования."""
        error = UnsupportedFileTypeError("test")
        
        self.assertIsInstance(error, MetadataCleanerError)
        self.assertIsInstance(error, Exception)


class TestMetadataProcessingError(unittest.TestCase):
    """Тесты для MetadataProcessingError."""

    def test_creation_with_metadata_type(self):
        """Тест создания ошибки с типом метаданных."""
        error = MetadataProcessingError("Failed to process EXIF data")
        
        self.assertIn("EXIF", str(error))
        self.assertIsInstance(error, MetadataCleanerError)

    def test_inheritance(self):
        """Тест наследования."""
        error = MetadataProcessingError("test")
        
        self.assertIsInstance(error, MetadataCleanerError)
        self.assertIsInstance(error, Exception)


class TestBackupError(unittest.TestCase):
    """Тесты для BackupError."""

    def test_creation_with_backup_operation(self):
        """Тест создания ошибки с операцией резервного копирования."""
        error = BackupError("Failed to create backup for file.jpg")
        
        self.assertIn("backup", str(error))
        self.assertIn("file.jpg", str(error))
        self.assertIsInstance(error, MetadataCleanerError)

    def test_inheritance(self):
        """Тест наследования."""
        error = BackupError("test")
        
        self.assertIsInstance(error, MetadataCleanerError)
        self.assertIsInstance(error, Exception)


class TestCorruptedFileError(unittest.TestCase):
    """Тесты для CorruptedFileError."""

    def test_creation_with_corrupted_file(self):
        """Тест создания ошибки поврежденного файла."""
        error = CorruptedFileError("File appears to be corrupted")
        
        self.assertIn("corrupted", str(error))
        self.assertIsInstance(error, MetadataCleanerError)

    def test_inheritance(self):
        """Тест наследования."""
        error = CorruptedFileError("test")
        
        self.assertIsInstance(error, MetadataCleanerError)
        self.assertIsInstance(error, Exception)


class TestEncryptedFileError(unittest.TestCase):
    """Тесты для EncryptedFileError."""

    def test_creation_with_encrypted_file(self):
        """Тест создания ошибки зашифрованного файла."""
        error = EncryptedFileError("File is password protected")
        
        self.assertIn("password protected", str(error))
        self.assertIsInstance(error, MetadataCleanerError)

    def test_inheritance(self):
        """Тест наследования."""
        error = EncryptedFileError("test")
        
        self.assertIsInstance(error, MetadataCleanerError)
        self.assertIsInstance(error, Exception)


class TestErrorsIntegration(unittest.TestCase):
    """Интеграционные тесты исключений."""

    def test_all_errors_are_catchable_by_base(self):
        """Тест что все ошибки можно поймать базовым исключением."""
        errors = [
            FileAccessError("test"),
            UnsupportedFileTypeError("test"),
            MetadataProcessingError("test"),
            BackupError("test"),
            CorruptedFileError("test"),
            EncryptedFileError("test"),
        ]

        for error in errors:
            with self.subTest(error_type=type(error).__name__):
                try:
                    raise error
                except MetadataCleanerError as caught:
                    self.assertIsInstance(caught, type(error))
                    self.assertEqual(str(caught), "test")

    def test_error_hierarchy(self):
        """Тест иерархии исключений."""
        custom_errors = [
            FileAccessError,
            UnsupportedFileTypeError,
            MetadataProcessingError,
            BackupError,
            CorruptedFileError,
            EncryptedFileError,
        ]

        for error_class in custom_errors:
            with self.subTest(error_class=error_class.__name__):
                self.assertTrue(issubclass(error_class, MetadataCleanerError))
                self.assertTrue(issubclass(error_class, Exception))


if __name__ == "__main__":
    unittest.main()
