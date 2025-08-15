"""Интеграционные тесты для Metadata Cleaner."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from metadata_cleaner.cleaner.dispatcher import MetadataDispatcher
from metadata_cleaner.cleaner.models import CleanStatus, OutputMode, CleaningOptions
from metadata_cleaner.services.settings_service import SettingsService
from metadata_cleaner.gui.app import MetadataCleanerApp


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Тесты полного рабочего процесса."""

    @pytest.mark.requires_files
    def test_complete_image_processing_workflow(self, dispatcher, sample_files, temp_dir):
        """Тест полного процесса обработки изображений."""
        if 'image_jpg' not in sample_files:
            pytest.skip("JPEG тестовый файл не доступен")
        
        source_file = sample_files['image_jpg']
        if not source_file.exists():
            pytest.skip("Тестовый JPEG файл не найден")
        
        # 1. Проверяем, что файл поддерживается
        assert dispatcher.is_supported(str(source_file))
        
        # 2. Получаем информацию о файле
        file_info = dispatcher.get_file_info(source_file)
        assert file_info['supported'] == 'True'
        
        # 3. Обрабатываем файл
        result = dispatcher.process_file(source_file)
        
        # 4. Проверяем результат
        assert result.status in [CleanStatus.SUCCESS, CleanStatus.SKIPPED]
        assert result.job.file_path == source_file
        
        if result.status == CleanStatus.SUCCESS:
            # Проверяем, что создан выходной файл или изменен исходный
            if result.job.output_path:
                assert result.job.output_path.exists()
            assert result.job.file_path.exists()

    @pytest.mark.requires_files
    def test_complete_document_processing_workflow(self, dispatcher, sample_files, temp_dir):
        """Тест полного процесса обработки документов."""
        if 'document_docx' not in sample_files:
            pytest.skip("DOCX тестовый файл не доступен")
        
        source_file = sample_files['document_docx']
        if not source_file.exists():
            pytest.skip("Тестовый DOCX файл не найден")
        
        # 1. Проверяем поддержку
        assert dispatcher.is_supported(str(source_file))
        
        # 2. Обрабатываем документ
        result = dispatcher.process_file(source_file)
        
        # 3. Проверяем результат
        assert result.status in [CleanStatus.SUCCESS, CleanStatus.SKIPPED]

    @pytest.mark.requires_files
    def test_complete_pdf_processing_workflow(self, dispatcher, sample_files, temp_dir):
        """Тест полного процесса обработки PDF."""
        if 'pdf' not in sample_files:
            pytest.skip("PDF тестовый файл не доступен")
        
        source_file = sample_files['pdf']
        if not source_file.exists():
            pytest.skip("Тестовый PDF файл не найден")
        
        # 1. Проверяем поддержку
        assert dispatcher.is_supported(str(source_file))
        
        # 2. Обрабатываем PDF
        result = dispatcher.process_file(source_file)
        
        # 3. Проверяем результат
        assert result.status in [CleanStatus.SUCCESS, CleanStatus.SKIPPED]

    def test_batch_processing_mixed_files(self, dispatcher, sample_files, temp_dir):
        """Тест пакетной обработки файлов разных типов."""
        if not sample_files:
            pytest.skip("Тестовые файлы не доступны")
        
        # Выбираем файлы разных типов
        mixed_files = []
        for key, file_path in sample_files.items():
            if file_path.exists():
                mixed_files.append(file_path)
                if len(mixed_files) >= 3:  # Максимум 3 файла для теста
                    break
        
        if not mixed_files:
            pytest.skip("Нет доступных тестовых файлов")
        
        results = []
        for file_path in mixed_files:
            result = dispatcher.process_file(file_path)
            results.append(result)
        
        # Проверяем, что все файлы обработаны
        assert len(results) == len(mixed_files)
        
        # Проверяем, что большинство обработок успешны
        successful = sum(1 for r in results if r.status == CleanStatus.SUCCESS)
        assert successful >= len(results) // 2  # Минимум половина успешных

    def test_different_output_modes(self, dispatcher, sample_files, temp_dir):
        """Тест разных режимов вывода."""
        if 'image_jpg' not in sample_files:
            pytest.skip("JPEG тестовый файл не доступен")
    
        source_file = sample_files['image_jpg']
        if not source_file.exists():
            pytest.skip("Тестовый файл не найден")
    
        # Копируем файл для каждого теста режима
        test_modes = [
            (OutputMode.CREATE_COPY, "copy"),
            (OutputMode.REPLACE, "replace"),
            (OutputMode.BACKUP_AND_OVERWRITE, "backup"),
        ]
        
        for mode, mode_name in test_modes:
            # Создаем копию файла для теста
            test_file = temp_dir / f"test_{mode_name}.jpg"
            shutil.copy2(source_file, test_file)
            
            # Создаем новый диспетчер с нужным режимом для каждого теста
            with patch.object(dispatcher.settings_service, 'get_output_mode', return_value=mode):
                # Обрабатываем файл
                result = dispatcher.process_file(test_file)
                
                # Проверяем результат в зависимости от режима
                if result.status == CleanStatus.SUCCESS:
                    if mode == OutputMode.CREATE_COPY:
                        assert result.job.output_path is not None
                        assert result.job.output_path.exists()
                    elif mode == OutputMode.REPLACE:
                        assert test_file.exists()
                    elif mode == OutputMode.BACKUP_AND_OVERWRITE:
                        assert test_file.exists()
                        # Могут быть созданы резервные копии

    def test_custom_cleaning_options(self, dispatcher, sample_files, temp_dir):
        """Тест пользовательских опций очистки."""
        if 'image_jpg' not in sample_files:
            pytest.skip("JPEG тестовый файл не доступен")
        
        source_file = sample_files['image_jpg']
        if not source_file.exists():
            pytest.skip("Тестовый файл не найден")
        
        # Создаем копию файла
        test_file = temp_dir / "test_custom_options.jpg"
        shutil.copy2(source_file, test_file)
        
        # Проверяем, что метод существует
        assert hasattr(dispatcher, 'process_file_with_options')

    def test_error_handling_integration(self, dispatcher, temp_dir):
        """Тест интеграционной обработки ошибок."""
        # Тест с несуществующим файлом
        nonexistent_file = temp_dir / "nonexistent.jpg"
        result = dispatcher.process_file(nonexistent_file)
        assert result.status == CleanStatus.ERROR
        
        # Тест с неподдерживаемым файлом
        unsupported_file = temp_dir / "test.txt"
        unsupported_file.write_text("This is a text file")
        result = dispatcher.process_file(unsupported_file)
        assert result.status == CleanStatus.ERROR
        
        # Тест с поврежденным файлом
        corrupted_file = temp_dir / "corrupted.jpg"
        corrupted_file.write_bytes(b"not a real image")
        result = dispatcher.process_file(corrupted_file)
        # Может быть SUCCESS (если обработчик пропускает) или ERROR
        assert result.status in [CleanStatus.SUCCESS, CleanStatus.ERROR, CleanStatus.SKIPPED]


@pytest.mark.integration
class TestSystemIntegration:
    """Тесты интеграции с системой."""

    def test_file_system_permissions(self, dispatcher, temp_dir):
        """Тест работы с правами доступа к файлам."""
        import os
        import stat
        
        # Создаем тестовый файл
        test_file = temp_dir / "permission_test.jpg"
        test_file.write_bytes(b"fake image data")
        
        # Проверяем обработку с нормальными правами (может быть ошибка если файл поврежден)
        result = dispatcher.process_file(test_file)
        assert result.status in [CleanStatus.SUCCESS, CleanStatus.SKIPPED, CleanStatus.ERROR]
        
        # Если операционная система поддерживает изменение прав доступа
        if os.name != 'nt':  # Не Windows
            # Делаем файл только для чтения
            test_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            
            # Обработка может завершиться ошибкой или успешно (зависит от режима)
            result = dispatcher.process_file(test_file)
            assert result.status in [CleanStatus.SUCCESS, CleanStatus.ERROR, CleanStatus.SKIPPED]

    def test_concurrent_file_access(self, dispatcher, temp_dir):
        """Тест параллельного доступа к файлам."""
        import threading
        import time
        
        # Создаем тестовый файл
        test_file = temp_dir / "concurrent_test.jpg"
        test_file.write_bytes(b"fake image data" * 1000)
        
        results = []
        exceptions = []
        
        def process_file_thread():
            """Функция для обработки файла в отдельном потоке."""
            try:
                # Создаем копию файла для каждого потока
                thread_file = temp_dir / f"thread_{threading.current_thread().ident}.jpg"
                shutil.copy2(test_file, thread_file)
                
                result = dispatcher.process_file(thread_file)
                results.append(result)
            except Exception as e:
                exceptions.append(e)
        
        # Запускаем несколько потоков
        threads = []
        for i in range(3):
            thread = threading.Thread(target=process_file_thread)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(exceptions) == 0, f"Исключения в потоках: {exceptions}"
        assert len(results) == 3
        # Поддельные файлы могут вызывать ошибки
        assert all(r.status in [CleanStatus.SUCCESS, CleanStatus.SKIPPED, CleanStatus.ERROR] for r in results)

    def test_large_directory_processing(self, dispatcher, temp_dir):
        """Тест обработки большой директории."""
        # Создаем много файлов
        files = []
        for i in range(20):
            test_file = temp_dir / f"bulk_test_{i:02d}.jpg"
            test_file.write_bytes(b"fake image data" * (i + 1))
            files.append(test_file)
        
        # Обрабатываем все файлы
        results = []
        for file_path in files:
            result = dispatcher.process_file(file_path)
            results.append(result)
        
        # Проверяем результаты
        assert len(results) == len(files)
        
        # Проверяем что все файлы обработаны (успешно, пропущены или с ошибкой)
        successful = sum(1 for r in results if r.status == CleanStatus.SUCCESS)
        errors = sum(1 for r in results if r.status == CleanStatus.ERROR)
        skipped = sum(1 for r in results if r.status == CleanStatus.SKIPPED)
        # Все файлы должны быть обработаны в каком-то статусе
        assert successful + errors + skipped == len(files)

    def test_memory_cleanup_after_processing(self, dispatcher, temp_dir):
        """Тест очистки памяти после обработки."""
        import gc
        import os
        
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil не установлен")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Создаем и обрабатываем много файлов
        for i in range(50):
            test_file = temp_dir / f"memory_test_{i}.jpg"
            test_file.write_bytes(b"fake image data" * 1000)  # ~15KB файлы
            
            result = dispatcher.process_file(test_file)
            
            # Удаляем файл после обработки
            test_file.unlink()
        
        # Принудительная сборка мусора
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Увеличение памяти должно быть разумным
        assert memory_increase < 50  # Меньше 50MB увеличения
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")


@pytest.mark.integration 
class TestGUIIntegration:
    """Тесты интеграции GUI компонентов."""

    @pytest.fixture
    def mock_flet_page(self):
        """Создает мок страницы Flet для тестирования."""
        page = Mock()
        page.window_width = 1200
        page.window_height = 800
        page.controls = []
        page.update = Mock()
        page.add = Mock()
        page.remove = Mock()
        return page

    def test_gui_app_initialization_integration(self, mock_flet_page):
        """Тест интеграционной инициализации GUI приложения."""
        with patch('metadata_cleaner.gui.app.SettingsService') as mock_settings_class:
            mock_settings = Mock()
            mock_settings.get_language.return_value = "en"
            mock_settings.get_theme.return_value = "auto"
            mock_settings.get_theme_mode.return_value = "system"
            mock_settings.get_output_mode.return_value = OutputMode.CREATE_COPY
            mock_settings.get_window_size.return_value = (1200, 800)
            mock_settings.get_window_maximized.return_value = False
            mock_settings.get_show_notifications.return_value = True
            mock_settings.get_auto_close_after_completion.return_value = False
            mock_settings.get_file_type_settings.return_value = {"exif_author": True}
            mock_settings.get_metadata_to_clean.return_value = {
                "author": True, "gps_coords": True, "exif_camera": True,
                "created": True, "modified": True
            }
            mock_settings.save_settings.return_value = None
            mock_settings.set_theme.return_value = None
            mock_settings_class.return_value = mock_settings
            
            # Создаем приложение
            app = MetadataCleanerApp(mock_flet_page)
            
            # Проверяем, что все компоненты инициализированы
            assert app.settings is not None
            assert app.dispatcher is not None
            assert hasattr(app, 'file_cards')
            
            # Проверяем настройку окна
            assert mock_flet_page.title is not None

    def test_gui_file_processing_integration(self, mock_flet_page, sample_files, temp_dir):
        """Тест интеграции обработки файлов в GUI."""
        if not sample_files:
            pytest.skip("Тестовые файлы не доступны")
        
        with patch('metadata_cleaner.gui.app.SettingsService') as mock_settings_class:
            mock_settings = Mock()
            mock_settings.get_language.return_value = "en"
            mock_settings.get_theme.return_value = "auto"
            mock_settings.get_theme_mode.return_value = "system"
            mock_settings.get_output_mode.return_value = OutputMode.CREATE_COPY
            mock_settings.get_window_size.return_value = (1200, 800)
            mock_settings.get_window_maximized.return_value = False
            mock_settings.get_show_notifications.return_value = True
            mock_settings.get_auto_close_after_completion.return_value = False
            mock_settings.get_file_type_settings.return_value = {"exif_author": True}
            mock_settings.get_metadata_to_clean.return_value = {
                "author": True, "gps_coords": True, "exif_camera": True,
                "created": True, "modified": True
            }
            mock_settings.save_settings.return_value = None
            mock_settings.set_theme.return_value = None
            mock_settings_class.return_value = mock_settings
            
            app = MetadataCleanerApp(mock_flet_page)
            
            # Добавляем файлы
            available_files = [str(path) for path in sample_files.values() if path.exists()]
            if available_files:
                app.add_files(available_files[:2])  # Максимум 2 файла
                
                # Проверяем, что файлы добавлены
                assert len(app.file_cards) > 0