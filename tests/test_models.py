"""Тесты для моделей данных."""

import unittest
from pathlib import Path
from datetime import datetime

from metadata_cleaner.cleaner.models import (
    CleanResult,
    CleanStatus,
    FileJob,
    FileType,
    OutputMode,
    CleaningOptions,
)


class TestFileType(unittest.TestCase):
    """Тесты для FileType enum."""

    def test_file_type_values(self):
        """Тест значений FileType."""
        self.assertEqual(FileType.IMAGE.value, "image")
        self.assertEqual(FileType.DOCUMENT.value, "document")
        self.assertEqual(FileType.PDF.value, "pdf")
        self.assertEqual(FileType.VIDEO.value, "video")

    def test_file_type_string_representation(self):
        """Тест строкового представления FileType."""
        self.assertEqual(str(FileType.IMAGE), "FileType.IMAGE")
        self.assertEqual(str(FileType.DOCUMENT), "FileType.DOCUMENT")
        self.assertEqual(str(FileType.PDF), "FileType.PDF")
        self.assertEqual(str(FileType.VIDEO), "FileType.VIDEO")


class TestCleanStatus(unittest.TestCase):
    """Тесты для CleanStatus enum."""

    def test_clean_status_values(self):
        """Тест значений CleanStatus."""
        self.assertEqual(CleanStatus.PENDING.value, "pending")
        self.assertEqual(CleanStatus.PROCESSING.value, "processing")
        self.assertEqual(CleanStatus.SUCCESS.value, "success")
        self.assertEqual(CleanStatus.ERROR.value, "error")

    def test_clean_status_ordering(self):
        """Тест порядка статусов обработки."""
        statuses = [CleanStatus.PENDING, CleanStatus.PROCESSING, CleanStatus.SUCCESS, CleanStatus.ERROR]
        for i, status in enumerate(statuses):
            self.assertEqual(status.value, ["pending", "processing", "success", "error"][i])


class TestOutputMode(unittest.TestCase):
    """Тесты для OutputMode enum."""

    def test_output_mode_values(self):
        """Тест значений OutputMode."""
        self.assertEqual(OutputMode.CREATE_COPY.value, "create_copy")
        self.assertEqual(OutputMode.REPLACE.value, "replace")
        self.assertEqual(OutputMode.BACKUP_AND_OVERWRITE.value, "backup_and_overwrite")


class TestFileJob(unittest.TestCase):
    """Тесты для FileJob модели."""

    def setUp(self):
        """Настройка тестовых данных."""
        self.test_path = Path("test_file.jpg")
        self.output_path = Path("output_file.jpg")

    def test_file_job_creation_minimal(self):
        """Тест создания FileJob с минимальными параметрами."""
        job = FileJob(file_path=self.test_path)

        self.assertEqual(job.file_path, self.test_path)
        self.assertEqual(job.file_type, FileType.UNKNOWN)  # По умолчанию UNKNOWN
        self.assertIsNone(job.output_path)
        self.assertTrue(job.backup_enabled)  # По умолчанию True
        self.assertIsInstance(job.clean_fields, dict)  # Заполняется в __post_init__

    def test_file_job_creation_full(self):
        """Тест создания FileJob со всеми параметрами."""
        clean_fields = {
            "author": True,
            "gps_coords": True,
            "created": True,
        }

        job = FileJob(
            file_path=self.test_path,
            file_type=FileType.IMAGE,
            output_path=self.output_path,
            backup_enabled=True,
            clean_fields=clean_fields,
        )

        self.assertEqual(job.file_path, self.test_path)
        self.assertEqual(job.file_type, FileType.IMAGE)
        self.assertEqual(job.output_path, self.output_path)
        self.assertTrue(job.backup_enabled)
        self.assertEqual(job.clean_fields, clean_fields)

    def test_file_job_with_different_file_types(self):
        """Тест FileJob с разными типами файлов."""
        test_cases = [
            (FileType.IMAGE, "test.jpg"),
            (FileType.DOCUMENT, "test.docx"),
            (FileType.PDF, "test.pdf"),
            (FileType.VIDEO, "test.mp4"),
        ]

        for file_type, filename in test_cases:
            with self.subTest(file_type=file_type):
                job = FileJob(
                    file_path=Path(filename),
                    file_type=file_type,
                )
                self.assertEqual(job.file_type, file_type)
                self.assertEqual(job.file_path.name, filename)

    def test_file_job_clean_fields_modification(self):
        """Тест изменения clean_fields после создания."""
        job = FileJob(file_path=self.test_path)
        
        # Изначально заполнен в __post_init__
        self.assertIsInstance(job.clean_fields, dict)
        self.assertGreater(len(job.clean_fields), 0)
        
        # Добавляем/изменяем поля
        job.clean_fields["test_field"] = True
        job.clean_fields["author"] = False
        
        self.assertTrue(job.clean_fields["test_field"])
        self.assertFalse(job.clean_fields["author"])

    def test_file_job_path_types(self):
        """Тест FileJob с разными типами путей."""
        # Строковый путь
        job1 = FileJob(file_path="test.jpg")
        self.assertIsInstance(job1.file_path, (str, Path))
        
        # Path объект
        job2 = FileJob(file_path=Path("test.jpg"))
        self.assertIsInstance(job2.file_path, Path)


class TestCleanResult(unittest.TestCase):
    """Тесты для CleanResult модели."""

    def setUp(self):
        """Настройка тестовых данных."""
        self.test_job = FileJob(
            file_path=Path("test.jpg"),
            file_type=FileType.IMAGE,
        )

    def test_clean_result_creation_minimal(self):
        """Тест создания CleanResult с минимальными параметрами."""
        result = CleanResult(
            job=self.test_job,
            status=CleanStatus.SUCCESS,
        )

        self.assertEqual(result.job, self.test_job)
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(result.message, "")  # Пустая строка по умолчанию
        self.assertIsNone(result.error)
        self.assertIsNone(result.cleaned_fields)  # None по умолчанию
        self.assertEqual(result.processing_time, 0.0)

    def test_clean_result_creation_full(self):
        """Тест создания CleanResult со всеми параметрами."""
        cleaned_fields = {"author": "removed", "gps_coords": "removed"}
        error_msg = "Test error"
        processing_time = 1.5

        result = CleanResult(
            job=self.test_job,
            status=CleanStatus.ERROR,
            message="Processing failed",
            error=error_msg,
            cleaned_fields=cleaned_fields,
            processing_time=processing_time,
        )

        self.assertEqual(result.job, self.test_job)
        self.assertEqual(result.status, CleanStatus.ERROR)
        self.assertEqual(result.message, "Processing failed")
        self.assertEqual(result.error, error_msg)
        self.assertEqual(result.cleaned_fields, cleaned_fields)
        self.assertEqual(result.processing_time, processing_time)

    def test_clean_result_different_statuses(self):
        """Тест CleanResult с разными статусами."""
        statuses = [
            CleanStatus.PENDING,
            CleanStatus.PROCESSING,
            CleanStatus.SUCCESS,
            CleanStatus.ERROR,
        ]

        for status in statuses:
            with self.subTest(status=status):
                result = CleanResult(job=self.test_job, status=status)
                self.assertEqual(result.status, status)

    def test_clean_result_success_with_cleaned_fields(self):
        """Тест успешного результата с очищенными полями."""
        cleaned_fields = {
            "author": "John Doe",
            "gps_coords": "55.7558,37.6173",
            "created": "2024-01-01 12:00:00",
            "camera_info": "Canon EOS R5",
        }

        result = CleanResult(
            job=self.test_job,
            status=CleanStatus.SUCCESS,
            message="Metadata cleaned successfully",
            cleaned_fields=cleaned_fields,
            processing_time=0.5,
        )

        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(len(result.cleaned_fields), 4)
        self.assertIn("author", result.cleaned_fields)
        self.assertIn("gps_coords", result.cleaned_fields)
        self.assertEqual(result.cleaned_fields["author"], "John Doe")

    def test_clean_result_error_with_details(self):
        """Тест результата с ошибкой и деталями."""
        error_details = "File is corrupted or not accessible"

        result = CleanResult(
            job=self.test_job,
            status=CleanStatus.ERROR,
            message="Failed to process file",
            error=error_details,
        )

        self.assertEqual(result.status, CleanStatus.ERROR)
        self.assertEqual(result.message, "Failed to process file")
        self.assertEqual(result.error, error_details)
        self.assertIsNone(result.cleaned_fields)  # None по умолчанию

    def test_clean_result_processing_time(self):
        """Тест времени обработки в результате."""
        processing_times = [0.1, 1.0, 5.5, 10.0]

        for time_val in processing_times:
            with self.subTest(processing_time=time_val):
                result = CleanResult(
                    job=self.test_job,
                    status=CleanStatus.SUCCESS,
                    processing_time=time_val,
                )
                self.assertEqual(result.processing_time, time_val)


class TestCleaningOptions(unittest.TestCase):
    """Тесты для CleaningOptions модели."""

    def test_cleaning_options_defaults(self):
        """Тест значений по умолчанию для CleaningOptions."""
        options = CleaningOptions()

        # Проверяем значения по умолчанию согласно реальной реализации
        self.assertTrue(options.clean_author)
        self.assertFalse(options.clean_title)  # False по умолчанию
        self.assertFalse(options.clean_subject)  # False по умолчанию
        self.assertFalse(options.clean_keywords)  # False по умолчанию
        self.assertTrue(options.clean_comments)
        self.assertTrue(options.clean_created_date)
        self.assertTrue(options.clean_modified_date)
        self.assertTrue(options.clean_gps_data)
        self.assertTrue(options.clean_camera_info)
        self.assertTrue(options.create_backup)  # True по умолчанию

    def test_cleaning_options_custom_values(self):
        """Тест CleaningOptions с пользовательскими значениями."""
        options = CleaningOptions(
            clean_author=False,
            clean_title=True,
            clean_subject=False,
            clean_keywords=True,
            clean_comments=False,
            clean_created_date=True,
            clean_modified_date=False,
            clean_gps_data=True,
            clean_camera_info=False,
            create_backup=True,
        )

        self.assertFalse(options.clean_author)
        self.assertTrue(options.clean_title)
        self.assertFalse(options.clean_subject)
        self.assertTrue(options.clean_keywords)
        self.assertFalse(options.clean_comments)
        self.assertTrue(options.clean_created_date)
        self.assertFalse(options.clean_modified_date)
        self.assertTrue(options.clean_gps_data)
        self.assertFalse(options.clean_camera_info)
        self.assertTrue(options.create_backup)

    def test_cleaning_options_all_enabled(self):
        """Тест CleaningOptions со всеми включенными опциями."""
        options = CleaningOptions(
            clean_author=True,
            clean_title=True,
            clean_subject=True,
            clean_keywords=True,
            clean_comments=True,
            clean_created_date=True,
            clean_modified_date=True,
            clean_gps_data=True,
            clean_camera_info=True,
            create_backup=True,
        )

        # Все опции должны быть включены
        option_fields = [
            "clean_author", "clean_title", "clean_subject", "clean_keywords",
            "clean_comments", "clean_created_date", "clean_modified_date",
            "clean_gps_data", "clean_camera_info", "create_backup"
        ]

        for field in option_fields:
            with self.subTest(field=field):
                self.assertTrue(getattr(options, field))

    def test_cleaning_options_all_disabled(self):
        """Тест CleaningOptions со всеми выключенными опциями."""
        options = CleaningOptions(
            clean_author=False,
            clean_title=False,
            clean_subject=False,
            clean_keywords=False,
            clean_comments=False,
            clean_created_date=False,
            clean_modified_date=False,
            clean_gps_data=False,
            clean_camera_info=False,
            create_backup=False,
        )

        # Все опции должны быть выключены
        option_fields = [
            "clean_author", "clean_title", "clean_subject", "clean_keywords",
            "clean_comments", "clean_created_date", "clean_modified_date",
            "clean_gps_data", "clean_camera_info", "create_backup"
        ]

        for field in option_fields:
            with self.subTest(field=field):
                self.assertFalse(getattr(options, field))

    def test_cleaning_options_privacy_focused(self):
        """Тест CleaningOptions с фокусом на приватность."""
        # Удаляем персональные данные, но сохраняем контент
        options = CleaningOptions(
            clean_author=True,
            clean_title=False,  # Сохраняем заголовки
            clean_subject=False,  # Сохраняем тематику
            clean_keywords=False,  # Сохраняем ключевые слова
            clean_comments=False,  # Сохраняем комментарии к контенту
            clean_created_date=True,  # Удаляем временные метки
            clean_modified_date=True,
            clean_gps_data=True,  # Удаляем геолокацию
            clean_camera_info=True,  # Удаляем информацию об устройстве
            create_backup=True,  # Создаем резервную копию
        )

        # Персональные данные удаляются
        self.assertTrue(options.clean_author)
        self.assertTrue(options.clean_created_date)
        self.assertTrue(options.clean_modified_date)
        self.assertTrue(options.clean_gps_data)
        self.assertTrue(options.clean_camera_info)
        self.assertTrue(options.create_backup)

        # Контент сохраняется
        self.assertFalse(options.clean_title)
        self.assertFalse(options.clean_subject)
        self.assertFalse(options.clean_keywords)
        self.assertFalse(options.clean_comments)


class TestModelsIntegration(unittest.TestCase):
    """Интеграционные тесты моделей."""

    def test_complete_workflow_models(self):
        """Тест полного рабочего процесса с моделями."""
        # Создаем задание
        job = FileJob(
            file_path=Path("test_image.jpg"),
            file_type=FileType.IMAGE,
            output_path=Path("test_image_cleaned.jpg"),
            backup_enabled=True,
            clean_fields={
                "author": True,
                "gps_coords": True,
                "camera_info": True,
            }
        )

        # Создаем результат обработки
        result = CleanResult(
            job=job,
            status=CleanStatus.SUCCESS,
            message="Image metadata cleaned successfully",
            cleaned_fields={
                "author": "John Photographer",
                "gps_coords": "55.7558,37.6173",
                "camera_info": "Canon EOS R5, f/2.8, ISO 100",
            },
            processing_time=0.75,
        )

        # Проверяем связность данных
        self.assertEqual(result.job.file_path, Path("test_image.jpg"))
        self.assertEqual(result.job.file_type, FileType.IMAGE)
        self.assertEqual(result.status, CleanStatus.SUCCESS)
        self.assertEqual(len(result.cleaned_fields), 3)
        self.assertIn("author", result.cleaned_fields)
        self.assertIn("gps_coords", result.cleaned_fields)
        self.assertIn("camera_info", result.cleaned_fields)

    def test_error_workflow_models(self):
        """Тест рабочего процесса с ошибкой."""
        job = FileJob(
            file_path=Path("corrupted_file.jpg"),
            file_type=FileType.IMAGE,
        )

        result = CleanResult(
            job=job,
            status=CleanStatus.ERROR,
            message="Failed to process corrupted file",
            error="PIL.UnidentifiedImageError: cannot identify image file",
            processing_time=0.1,
        )

        self.assertEqual(result.status, CleanStatus.ERROR)
        self.assertIsNotNone(result.error)
        self.assertIsNone(result.cleaned_fields)  # None по умолчанию
        self.assertIsNotNone(result.processing_time)

    def test_options_to_job_conversion(self):
        """Тест конвертации опций в параметры задания."""
        options = CleaningOptions(
            clean_author=True,
            clean_gps_data=True,
            clean_camera_info=False,
            clean_title=False,
            create_backup=True,
        )

        # Симулируем конвертацию опций в clean_fields
        clean_fields = {
            "author": options.clean_author,
            "gps_coords": options.clean_gps_data,
            "camera_info": options.clean_camera_info,
            "title": options.clean_title,
        }

        job = FileJob(
            file_path=Path("test.jpg"),
            backup_enabled=options.create_backup,
            clean_fields=clean_fields,
        )

        self.assertTrue(job.backup_enabled)
        self.assertTrue(job.clean_fields["author"])
        self.assertTrue(job.clean_fields["gps_coords"])
        self.assertFalse(job.clean_fields["camera_info"])
        self.assertFalse(job.clean_fields["title"])


if __name__ == "__main__":
    unittest.main()
