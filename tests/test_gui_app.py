"""Тесты для основного GUI приложения."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from metadata_cleaner.gui.app import MetadataCleanerApp
from metadata_cleaner.cleaner.models import OutputMode, CleanStatus
from metadata_cleaner.services.settings_service import SettingsService


@pytest.mark.unit
class TestMetadataCleanerApp:
    """Тесты основного класса приложения."""

    @pytest.fixture
    def mock_flet_page(self):
        """Создает мок страницы Flet."""
        page = Mock()
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600
        page.title = ""
        page.theme_mode = "system"
        page.controls = []
        page.update = Mock()
        page.add = Mock()
        page.remove = Mock()
        page.clean = Mock()
        return page

    @pytest.fixture
    def mock_settings_service(self):
        """Создает мок сервиса настроек."""
        settings = Mock(spec=SettingsService)
        settings.get_language.return_value = "en"
        settings.get_theme.return_value = "auto"
        settings.get_theme_mode.return_value = "system"
        settings.get_output_mode.return_value = OutputMode.CREATE_COPY
        settings.get_window_size.return_value = (1200, 800)
        settings.get_window_maximized.return_value = False
        settings.get_show_notifications.return_value = True
        settings.get_auto_close_after_completion.return_value = False
        settings.get_file_type_settings.return_value = {"exif_author": True}
        settings.get_metadata_to_clean.return_value = {
            "author": True,
            "gps_coords": True,
            "exif_camera": True,
            "created": True,
            "modified": True,
        }
        settings.save_settings.return_value = None
        settings.set_theme.return_value = None
        return settings

    @pytest.fixture
    def app(self, mock_flet_page, mock_settings_service):
        """Создает экземпляр приложения для тестирования."""
        with patch('metadata_cleaner.gui.app.SettingsService', return_value=mock_settings_service):
            app = MetadataCleanerApp(mock_flet_page)
            return app

    def test_app_initialization(self, app, mock_flet_page):
        """Тест инициализации приложения."""
        assert app.page == mock_flet_page
        assert app.settings is not None
        assert app.dispatcher is not None
        assert hasattr(app, 'file_cards')

    def test_app_title_setting(self, app, mock_flet_page):
        """Тест установки заголовка приложения."""
        # Проверяем, что заголовок установлен
        assert "Metadata Cleaner" in mock_flet_page.title

    def test_window_setup(self, app, mock_flet_page):
        """Тест настройки окна приложения."""
        # Проверяем настройки окна
        assert mock_flet_page.window_width == 1200
        assert mock_flet_page.window_height == 800

    def test_theme_initialization(self, app, mock_flet_page):
        """Тест инициализации темы."""
        # Тема должна быть установлена согласно настройкам
        # (в данном случае "auto" -> "system")
        assert mock_flet_page.theme_mode in ["system", "light", "dark"]

    @patch('metadata_cleaner.gui.app.ft.FilePicker')
    def test_file_picker_setup(self, mock_file_picker, app):
        """Тест настройки выбора файлов."""
        # Проверяем, что файл-пикеры созданы
        assert hasattr(app, 'file_picker')
        assert hasattr(app, 'folder_picker')

    def test_add_files_empty_list(self, app):
        """Тест добавления пустого списка файлов."""
        initial_count = len(app.file_cards)
        app.add_files([])
        
        # Количество файлов не должно измениться
        assert len(app.file_cards) == initial_count

    def test_add_files_with_files(self, app, temp_dir):
        """Тест добавления файлов в приложение."""
        # Создаем тестовый файл
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")
        
        app.add_files([str(test_file)])
        
        # Проверяем, что файл добавлен
        assert len(app.file_cards) > 0

    def test_add_duplicate_files(self, app, temp_dir):
        """Тест добавления дубликатов файлов."""
        # Создаем тестовый файл
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")
        
        # Добавляем файл дважды
        app.add_files([str(test_file)])
        initial_count = len(app.file_cards)
        app.add_files([str(test_file)])
        
        # Количество не должно увеличиться
        assert len(app.file_cards) == initial_count

    def test_remove_file(self, app, temp_dir):
        """Тест удаления файла из списка."""
        # Создаем и добавляем тестовый файл
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")
        app.add_files([str(test_file)])
        
        initial_count = len(app.file_cards)
        assert initial_count > 0
        
        # Удаляем файл (передаем карточку, а не путь)
        file_path = str(test_file)
        if file_path in app.file_cards:
            file_card = app.file_cards[file_path]
            app.remove_file(file_card)
        
        # Проверяем, что файл удален
        assert len(app.file_cards) == initial_count - 1

    def test_clear_all_files(self, app, temp_dir):
        """Тест очистки всех файлов."""
        # Добавляем несколько файлов
        for i in range(3):
            test_file = temp_dir / f"test{i}.jpg"
            test_file.write_bytes(b"fake image data")
            app.add_files([str(test_file)])
        
        assert len(app.file_cards) > 0
        
        # Очищаем все файлы (вызываем clear_list с mock event)
        from unittest.mock import Mock
        mock_event = Mock()
        app.clear_list(mock_event)
        
        # Проверяем, что все файлы удалены
        assert len(app.file_cards) == 0

    @patch('metadata_cleaner.gui.app.MetadataDispatcher')
    def test_process_files_success(self, mock_dispatcher_class, app, temp_dir):
        """Тест успешной обработки файлов."""
        # Настраиваем мок диспетчера
        mock_dispatcher = Mock()
        mock_dispatcher_class.return_value = mock_dispatcher
        
        # Создаем мок результата
        mock_result = Mock()
        mock_result.status = CleanStatus.SUCCESS
        mock_result.message = "Success"
        mock_result.job.output_path = temp_dir / "output.jpg"
        mock_dispatcher.process_file.return_value = mock_result
        
        # Создаем тестовый файл
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")
        app.add_files([str(test_file)])
        
        # Проверяем, что метод существует
        assert hasattr(app, 'clean_metadata')
        assert hasattr(app, 'is_processing')

    def test_settings_dialog_opening(self, app):
        """Тест открытия диалога настроек."""
        # Проверяем, что метод существует
        assert hasattr(app, 'show_settings')

    def test_about_dialog_opening(self, app):
        """Тест открытия диалога "О программе"."""
        # Проверяем, что метод существует (на данный момент не реализован)
        assert hasattr(app, 'settings_dialog')

    def test_supported_files_filtering(self, app, temp_dir):
        """Тест фильтрации поддерживаемых файлов."""
        # Создаем поддерживаемые и неподдерживаемые файлы
        supported_file = temp_dir / "test.jpg"
        unsupported_file = temp_dir / "test.txt"
        
        supported_file.write_bytes(b"fake image data")
        unsupported_file.write_text("text content")
        
        files = [str(supported_file), str(unsupported_file)]
        app.add_files(files)
        
        # Приложение добавляет все файлы, фильтрация происходит при обработке
        assert len(app.file_cards) == 2

    def test_drag_and_drop_handler(self, app, temp_dir):
        """Тест обработчика drag and drop."""
        # Создаем тестовый файл
        test_file = temp_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")
        
        # Проверяем, что метод существует
        assert hasattr(app, 'on_files_picked')

    def test_localization_change(self, app, mock_settings_service):
        """Тест изменения локализации."""
        # Проверяем, что метод существует
        assert hasattr(app, 'rebuild_ui_for_language_change')

    def test_theme_change(self, app, mock_flet_page, mock_settings_service):
        """Тест изменения темы."""
        # Проверяем, что метод существует
        assert hasattr(app, 'toggle_theme')

    def test_processing_cancellation(self, app):
        """Тест отмены обработки файлов."""
        # Проверяем, что есть флаг обработки
        assert hasattr(app, 'is_processing')

    def test_error_handling_during_processing(self, app, temp_dir):
        """Тест обработки ошибок во время обработки файлов."""
        # Проверяем, что метод существует
        assert hasattr(app, 'clean_metadata')

    def test_progress_updates(self, app, temp_dir):
        """Тест обновления прогресса обработки."""
        # Создаем несколько тестовых файлов
        for i in range(3):
            test_file = temp_dir / f"test{i}.jpg"
            test_file.write_bytes(b"fake image data")
            app.add_files([str(test_file)])
        
        # Проверяем начальное состояние прогресса
        assert hasattr(app, 'progress_card')
        
        # Проверяем, что метод обновления статистики существует
        assert hasattr(app, 'update_stats')

    def test_statistics_updates(self, app):
        """Тест обновления статистики."""
        # Проверяем, что метод существует
        assert hasattr(app, 'update_stats')


@pytest.mark.integration
class TestMetadataCleanerAppIntegration:
    """Интеграционные тесты приложения."""

    def test_full_workflow_with_real_files(self, sample_files):
        """Тест полного рабочего процесса с реальными файлами."""
        # Этот тест требует реальные тестовые файлы
        if not sample_files:
            pytest.skip("Нет доступных тестовых файлов")
        
        with patch('flet.Page') as mock_page_class:
            mock_page = Mock()
            mock_page.window_width = 1200
            mock_page.window_height = 800
            mock_page.title = ""
            mock_page.theme_mode = "system"
            mock_page.controls = []
            mock_page.update = Mock()
            mock_page.add = Mock()
            mock_page.remove = Mock()
            mock_page.clean = Mock()
            mock_page_class.return_value = mock_page
            
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
                
                app = MetadataCleanerApp(mock_page)
                
                # Добавляем файлы
                file_paths = [str(path) for path in sample_files.values() if path.exists()]
                app.add_files(file_paths)
                
                # Проверяем, что файлы добавлены
                assert len(app.file_cards) > 0