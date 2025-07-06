from __future__ import annotations

import asyncio
from pathlib import Path

import flet as ft

from metadata_cleaner.cleaner.dispatcher import MetadataDispatcher
from metadata_cleaner.cleaner.models import (
    CleanResult,
    CleanStatus,
    FileJob,
)
from metadata_cleaner.gui.components.action_bar import ActionBar
from metadata_cleaner.gui.components.detailed_results_dialog import DetailedResultsDialog
from metadata_cleaner.gui.components.file_card import FileCard
from metadata_cleaner.gui.components.progress_card import ProgressCard
from metadata_cleaner.gui.components.settings_dialog import SettingsDialog
from metadata_cleaner.gui.components.stats_panel import StatsPanel
from metadata_cleaner.gui.localization import translator
from metadata_cleaner.services.settings_service import SettingsService
from metadata_cleaner.version import get_version


class MetadataCleanerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_files = []
        self.cleaning_results = {}
        self.file_cards = {}
        self.is_processing = False  # Флаг активной обработки

        self.settings = SettingsService()
        self.dispatcher = MetadataDispatcher(settings_service=self.settings)
        
        # Диалог детальных результатов
        self.detailed_results_dialog = DetailedResultsDialog()

        # Установка языка из настроек
        translator.set_language(self.settings.get_language())

        self.setup_page()
        self.build_ui()

    def setup_page(self):
        """Настройка страницы"""
        self.page.title = f"{translator.get('app_title')} v{get_version()}"

        # Загружаем размеры окна из настроек
        width, height = self.settings.get_window_size()
        self.page.window_width = width
        self.page.window_height = height
        self.page.window_min_width = 800
        self.page.window_min_height = 600

        self.page.padding = 0
        self.page.spacing = 0

        # Современная Material Design 3 цветовая схема
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.colors.DEEP_PURPLE,
            use_material3=True,
            visual_density=ft.ThemeVisualDensity.COMPACT,
        )

        # Темная тема с адаптивными цветами
        self.page.dark_theme = ft.Theme(
            color_scheme_seed=ft.colors.DEEP_PURPLE,
            use_material3=True,
            visual_density=ft.ThemeVisualDensity.COMPACT,
        )

        # Настройка темы из настроек
        theme = self.settings.get_theme()
        if theme == "system":
            self.page.theme_mode = ft.ThemeMode.SYSTEM
        elif theme == "light":
            self.page.theme_mode = ft.ThemeMode.LIGHT
        elif theme == "dark":
            self.page.theme_mode = ft.ThemeMode.DARK

        # Настройка шрифтов
        self.page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"
        }

        # Настройка файл пикера
        self.file_picker = ft.FilePicker(on_result=self.on_files_picked)
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_picked)

        self.page.overlay.extend([self.file_picker, self.folder_picker])

    def build_ui(self):
        """Построение интерфейса"""
        # Создание компонентов
        self.action_bar = ActionBar(
            on_pick_files=self.pick_files,
            on_pick_folder=self.pick_folder,
            on_clear_list=self.clear_list,
            on_clean_metadata=self.clean_metadata,
            on_show_details=self.show_detailed_results,
        )

        self.stats_panel = StatsPanel()
        self.progress_card = ProgressCard()

        # Возвращаем GridView как было
        self.files_grid = ft.GridView(
            expand=True,
            runs_count=0,  # Автоматическое количество колонок
            max_extent=250,  # Ширина карточек
            child_aspect_ratio=1.4,  # Соотношение сторон карточки
            spacing=8,
            run_spacing=8,
        )

        # Создаем переменные для текстов пустого состояния
        self.empty_state_title = ft.Text(
            translator.get("ready_to_work"),
            size=18,
            weight=ft.FontWeight.W_500,
            color=ft.colors.ON_SURFACE_VARIANT,
        )
        self.empty_state_subtitle = ft.Text(
            translator.get("use_buttons_to_select"),
            size=14,
            color=ft.colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        )

        # Простая область для пустого состояния
        self.empty_files_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.icons.UPLOAD_FILE_OUTLINED, size=64, color=ft.colors.OUTLINE
                    ),
                    self.empty_state_title,
                    self.empty_state_subtitle,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.alignment.center,
            height=300,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=12,
            padding=ft.padding.all(32),
            margin=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Контейнер для GridView с прокруткой
        self.files_container = ft.Container(
            content=self.files_grid,
            visible=False,  # Изначально скрыт
            expand=True,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # Создание диалога настроек
        self.settings_dialog = SettingsDialog(
            page=self.page, on_save=self.on_settings_save
        )

        # Загружаем текущие настройки в диалог
        self.settings_dialog.current_settings = self.settings.get_all_settings()

        # Создаем переменные для элементов заголовка
        self.app_title_text = ft.Text(
            translator.get("app_title"),
            size=28,
            weight=ft.FontWeight.W_600,
            color=ft.colors.ON_SURFACE,
        )
        self.theme_button = ft.IconButton(
            icon=ft.icons.BRIGHTNESS_6,
            tooltip=translator.get("switch_theme"),
            on_click=self.toggle_theme,
        )
        self.settings_button = ft.IconButton(
            icon=ft.icons.SETTINGS,
            tooltip=translator.get("settings"),
            on_click=self.show_settings,
        )
        self.selected_files_text = ft.Text(
            translator.get("selected_files"),
            size=16,
            weight=ft.FontWeight.W_500,
            color=ft.colors.ON_SURFACE,
        )

        # Основной макет
        content = ft.Container(
            content=ft.Column(
                [
                    # Заголовок
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.CLEANING_SERVICES_ROUNDED,
                                    size=32,
                                    color=ft.colors.PRIMARY,
                                ),
                                self.app_title_text,
                                ft.Container(expand=True),
                                self.theme_button,
                                self.settings_button,
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=ft.padding.symmetric(horizontal=20, vertical=16),
                    ),
                    # Панель действий
                    ft.Container(
                        content=self.action_bar,
                        padding=ft.padding.symmetric(horizontal=20),
                    ),
                    ft.Divider(height=20),
                    # Основное содержимое - фиксированная высота
                    ft.Container(
                        content=ft.Row(
                            [
                                # Левая панель - АБСОЛЮТНО фиксированная
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            self.stats_panel,
                                            ft.Container(height=20),
                                            self.progress_card,
                                        ],
                                        spacing=0,
                                    ),
                                    width=300,
                                    height=600,  # Увеличена высота
                                    padding=ft.padding.all(16),
                                    alignment=ft.alignment.top_left,
                                ),
                                # Вертикальный разделитель
                                ft.VerticalDivider(width=1),
                                # Правая панель с файлами
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            # Заголовок списка файлов
                                            ft.Container(
                                                content=ft.Row(
                                                    [
                                                        ft.Icon(
                                                            ft.icons.FOLDER_OUTLINED,
                                                            size=20,
                                                        ),
                                                        self.selected_files_text,
                                                    ],
                                                    spacing=8,
                                                ),
                                                padding=ft.padding.only(
                                                    left=16, top=16, right=16, bottom=8
                                                ),
                                            ),
                                            # Контейнер с файлами - БЕЗ Stack!
                                            self.empty_files_container,
                                            # GridView файлов с прокруткой - ОТДЕЛЬНО!
                                            self.files_container,
                                        ],
                                        expand=True,
                                    ),
                                    expand=True,
                                ),
                            ],
                            expand=True,
                            spacing=0,
                        ),
                        height=600,  # Фиксированная общая высота
                    ),
                ],
                expand=True,
            ),
            padding=ft.padding.all(0),
        )

        self.page.add(content)
        self.update_empty_state()

    def update_empty_state(self):
        """Обновление состояния пустого списка"""
        has_files = len(self.selected_files) > 0

        # Обновляем видимость контейнеров
        self.empty_files_container.visible = not has_files
        self.files_container.visible = has_files

        if hasattr(self, "page") and self.page:
            self.page.update()

    def pick_files(self, e):
        """Выбор файлов"""
        self.file_picker.pick_files(
            dialog_title=translator.get("pick_files_dialog_title"),
            allow_multiple=True,
            allowed_extensions=[
                "jpg",
                "jpeg",
                "png",
                "gif",
                "heic",
                "heif",
                "pdf",
                "docx",
                "pptx",
                "xlsx",
                "mp4",
                "mov",
            ],
        )

    def pick_folder(self, e):
        """Выбор папки"""
        self.folder_picker.get_directory_path(
            dialog_title=translator.get("pick_folder_dialog_title")
        )

    def on_files_picked(self, e: ft.FilePickerResultEvent):
        """Обработка выбора файлов"""
        if e.files:
            file_paths = [f.path for f in e.files]
            self.add_files(file_paths)

    def on_folder_picked(self, e: ft.FilePickerResultEvent):
        """Обработка выбранной папки"""
        if e.path:
            folder_path = Path(e.path)
            supported_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".heic",
                ".heif",
                ".pdf",
                ".docx",
                ".pptx",
                ".xlsx",
                ".mp4",
                ".mov",
            }

            # Показываем уведомление о начале сканирования
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    translator.get("scanning_folder"), color=ft.colors.BLUE_800
                ),
                bgcolor=ft.colors.BLUE_100,
            )
            self.page.snack_bar.open = True
            self.page.update()

            new_files = []
            total_found = 0

            # Рекурсивный поиск во всех подпапках
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    total_found += 1
                    if (
                        file_path.suffix.lower() in supported_extensions
                        and str(file_path) not in self.selected_files
                    ):
                        new_files.append(str(file_path))

            # Показываем результат сканирования
            if new_files:
                self.add_files(new_files)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        translator.get(
                            "files_found", count=len(new_files), total=total_found
                        ),
                        color=ft.colors.GREEN_800,
                    ),
                    bgcolor=ft.colors.GREEN_100,
                )
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        translator.get("no_files_found", total=total_found),
                        color=ft.colors.ORANGE_800,
                    ),
                    bgcolor=ft.colors.ORANGE_100,
                )

            self.page.snack_bar.open = True
            self.page.update()

    def add_files(self, file_paths: list[str]):
        """Добавление файлов в список"""
        new_files_count = 0
        duplicates_count = 0

        for file_path in file_paths:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)

                card = FileCard(
                    file_path=file_path,
                    on_remove=self.remove_file,
                )

                self.file_cards[file_path] = card
                self.files_grid.controls.append(card)
                new_files_count += 1
            else:
                duplicates_count += 1

        # Показываем информацию если добавили новые файлы
        if new_files_count > 0:
            if duplicates_count > 0:
                message = translator.get(
                    "files_added_with_duplicates",
                    count=new_files_count,
                    duplicates=duplicates_count,
                )
            else:
                message = translator.get("files_added", count=new_files_count)

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message, color=ft.colors.GREEN_800),
                bgcolor=ft.colors.GREEN_100,
            )
            self.page.snack_bar.open = True

        self.update_ui()
        self.update_empty_state()

    def remove_file(self, card: FileCard):
        """Удаление файла из списка"""
        file_path = card.file_path
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)

            # Удаление карточки
            if file_path in self.file_cards:
                if card in self.files_grid.controls:
                    self.files_grid.controls.remove(card)
                del self.file_cards[file_path]

            # Удаление результата
            if file_path in self.cleaning_results:
                del self.cleaning_results[file_path]

        self.update_ui()
        self.update_empty_state()

    def clear_list(self, e):
        """Очистка списка файлов"""
        self.selected_files.clear()
        self.cleaning_results.clear()
        self.file_cards.clear()
        self.files_grid.controls.clear()
        
        # Скрываем кнопку деталей
        self.action_bar.set_details_visible(False)
        
        self.update_ui()
        self.update_empty_state()

    def update_ui(self):
        """Обновление интерфейса"""
        self.update_stats()
        self.update_clean_button()
        self.page.update()

    def update_clean_button(self):
        """Обновление состояния кнопки очистки"""
        has_files = len(self.selected_files) > 0

        # Используем правильный API ActionBar
        self.action_bar.set_clean_enabled(has_files)
        self.action_bar.update_button_state(has_files)

        if hasattr(self, "page") and self.page:
            self.page.update()

    def update_stats(self):
        """Обновление статистики"""
        total_files = len(self.selected_files)
        processed_files = len(self.cleaning_results)
        successful = sum(1 for r in self.cleaning_results.values() if r.is_success)
        failed = processed_files - successful

        # Обновляем панель статистики
        self.stats_panel.update_stats(total_files, processed_files, successful, failed)

        # Обновляем прогресс карточку
        if total_files == 0:
            self.progress_card.update_progress(
                translator.get("ready_to_work"), translator.get("select_files_to_start")
            )
        elif processed_files == 0:
            self.progress_card.update_progress(
                translator.get("files_selected"),
                translator.get("ready_to_process_files", count=total_files),
            )
        elif processed_files < total_files:
            if self.is_processing:
                # Во время активной обработки - только простое сообщение
                self.progress_card.update_progress(translator.get("processing_now"), "")
            else:
                # После завершения - показываем детали
                self.progress_card.update_progress(
                    translator.get("processing_now"),
                    translator.get(
                        "processed_files_count",
                        processed=processed_files,
                        total=total_files,
                    ),
                )
        else:
            if failed == 0:
                self.progress_card.show_success(
                    translator.get("done"),
                    translator.get("all_files_processed", count=total_files),
                )
            else:
                self.progress_card.show_error(
                    translator.get("completed_with_errors"),
                    translator.get(
                        "success_count_errors_count", success=successful, failed=failed
                    ),
                )

    async def clean_metadata(self, e):
        """Очистка метаданных"""

        if not self.selected_files:
            return

        # Устанавливаем состояние обработки
        self.is_processing = True
        self.action_bar.set_processing_state(True)
        self.action_bar.set_details_visible(False)  # Скрываем кнопку деталей во время обработки
        self.progress_card.reset()
        self.progress_card.update_progress(
            translator.get("starting_cleanup"), translator.get("preparing_files")
        )
        self.cleaning_results.clear()

        # Сброс статуса всех карточек
        for card in self.file_cards.values():
            card.cleaning_result = None
            card.update()  # Обновляем карточку

        self.page.update()

        total_files = len(self.selected_files)

        for _i, file_path in enumerate(self.selected_files):
            Path(file_path).name

            # Простое обновление без детальной информации
            self.progress_card.update_progress(
                translator.get("processing_now"),
                "",  # Пустая строка вместо деталей
            )
            self.page.update()

            try:
                result = await asyncio.to_thread(
                    self.dispatcher.process_file, Path(file_path)
                )
                self.cleaning_results[file_path] = result

                # Обновление карточки файла
                if file_path in self.file_cards:
                    self.file_cards[file_path].update_cleaning_result(result)

            except Exception as ex:
                job = FileJob(file_path=Path(file_path))
                result = CleanResult(
                    job=job, status=CleanStatus.ERROR, message=str(ex), error=ex
                )
                self.cleaning_results[file_path] = result

                # Обновление карточки файла
                if file_path in self.file_cards:
                    self.file_cards[file_path].update_cleaning_result(result)

            self.update_stats()
            await asyncio.sleep(0.1)

        # Завершение обработки
        self.is_processing = False
        self.action_bar.set_processing_state(False)
        successful = sum(1 for r in self.cleaning_results.values() if r.is_success)

        # Финальное обновление статистики покажет результат
        self.update_stats()

        # Показываем кнопку деталей после завершения обработки
        self.action_bar.set_details_visible(True)
        
        # Обновляем результаты в диалоге деталей
        self.detailed_results_dialog.update_results(self.cleaning_results)

        # Анимация успеха на кнопке
        if successful == total_files:
            self.action_bar.show_success_animation()

        self.page.update()
        self.show_completion_snackbar(successful, total_files)

    def show_completion_snackbar(self, successful: int, total: int):
        """Показ уведомления о завершении"""
        if successful == total:
            message = translator.get("completion_all_success", total=total)
            bgcolor = ft.colors.GREEN_100
        else:
            message = translator.get(
                "completion_with_errors", successful=successful, total=total
            )
            bgcolor = ft.colors.ORANGE_100

        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.colors.BLACK87),
            bgcolor=bgcolor,
        )

        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()

    def show_detailed_results(self, e=None):
        """Показ детальных результатов"""
        self.detailed_results_dialog.update_results(self.cleaning_results)
        self.detailed_results_dialog.show(self.page)

    def toggle_theme(self, e):
        """Переключение темы"""
        # Получаем текущие настройки темы
        current_theme = self.settings.get_theme()

        # Определяем текущую фактическую тему
        current_is_dark = False

        if current_theme == "dark":
            current_is_dark = True
        elif current_theme == "light":
            current_is_dark = False
        else:  # system
            # Используем platform_brightness для определения системной темы
            if hasattr(self.page, "platform_brightness"):
                current_is_dark = self.page.platform_brightness == ft.Brightness.DARK
            else:
                current_is_dark = False

        # Переключаем на противоположную тему
        if current_is_dark:
            new_theme = "light"
            self.page.theme_mode = ft.ThemeMode.LIGHT
        else:
            new_theme = "dark"
            self.page.theme_mode = ft.ThemeMode.DARK

        # Сохраняем тему в настройках
        self.settings.set_theme(new_theme)

        # Обновляем настройки в диалоге
        current_settings = self.settings.get_all_settings()
        self.settings_dialog.update_settings(current_settings)

        self.page.update()

    def show_settings(self, e):
        """Показ настроек"""
        # Получаем актуальные настройки перед показом диалога
        current_settings = {
            "theme": self.settings.get_theme(),
            "output_mode": self.settings.get_output_mode().value,
            "language": self.settings.get_language(),
            "file_type_settings": {
                "image": self.settings.get_file_type_settings("image"),
                "document": self.settings.get_file_type_settings("document"),
                "pdf": self.settings.get_file_type_settings("pdf"),
                "video": self.settings.get_file_type_settings("video"),
            },
        }
        # Обновляем настройки в диалоге
        self.settings_dialog.update_settings(current_settings)
        self.settings_dialog.show()

    def on_settings_save(self, settings: dict):
        """Обработка сохранения настроек"""
        self.settings.update_settings(settings)

        # Применяем тему если изменилась
        theme = settings.get("theme", "system")
        if theme == "system":
            self.page.theme_mode = ft.ThemeMode.SYSTEM
        elif theme == "light":
            self.page.theme_mode = ft.ThemeMode.LIGHT
        elif theme == "dark":
            self.page.theme_mode = ft.ThemeMode.DARK

        # Обновление языка ПЕРЕД показом уведомления
        new_lang = settings.get("language", "ru")
        language_changed = translator.language != new_lang
        if language_changed:
            translator.set_language(new_lang)
            self.rebuild_ui_for_language_change(keep_settings_open=True)

        # Показываем уведомление уже на правильном языке
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(
                translator.get("settings_saved"), color=ft.colors.GREEN_800
            ),
            bgcolor=ft.colors.GREEN_100,
            action=translator.get("ok"),
            action_color=ft.colors.GREEN,
        )
        self.page.snack_bar.open = True

        self.page.update()

    def get_file_icon(self, file_path: str) -> ft.Icon:
        """Получение иконки в зависимости от типа файла"""
        ext = Path(file_path).suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif"]:
            return ft.Icon(ft.icons.IMAGE, color=ft.colors.BLUE_GREY_400)
        elif ext in [".docx", ".xlsx", ".pptx"]:
            return ft.Icon(ft.icons.DESCRIPTION, color=ft.colors.BLUE_400)
        elif ext == ".pdf":
            return ft.Icon(ft.icons.PICTURE_AS_PDF, color=ft.colors.RED_400)
        elif ext in [".mp4", ".mov"]:
            return ft.Icon(ft.icons.VIDEOCAM, color=ft.colors.PURPLE_400)
        else:
            return ft.Icon(ft.icons.INSERT_DRIVE_FILE, color=ft.colors.GREY)

    def rebuild_ui_for_language_change(self, keep_settings_open=False):
        """Пересобирает UI для смены языка"""
        # Закрываем диалог настроек если он открыт (кроме случая когда нужно оставить открытым)
        settings_was_open = False
        if (
            hasattr(self, "settings_dialog")
            and self.settings_dialog.dialog
            and self.settings_dialog.dialog.open
        ):
            settings_was_open = True
            if not keep_settings_open:
                self.settings_dialog.dialog.open = False

        # Сохраняем список файлов перед перестройкой
        saved_files = self.selected_files.copy()
        saved_results = self.cleaning_results.copy()

        # Обновляем заголовок страницы
        self.page.title = f"{translator.get('app_title')} v{get_version()}"

        # Обновляем все текстовые элементы интерфейса
        self.app_title_text.value = translator.get("app_title")
        self.theme_button.tooltip = translator.get("switch_theme")
        self.settings_button.tooltip = translator.get("settings")
        self.selected_files_text.value = translator.get("selected_files")
        self.empty_state_title.value = translator.get("ready_to_work")
        self.empty_state_subtitle.value = translator.get("use_buttons_to_select")

        # Пересобираем UI компоненты с новыми переводами
        self.action_bar.rebuild()
        self.stats_panel.rebuild()
        self.progress_card.rebuild()

        # Восстанавливаем файлы
        self.selected_files = saved_files
        self.cleaning_results = saved_results

        # Пересоздаем карточки файлов с новыми переводами
        for file_path in self.selected_files:
            if file_path in self.file_cards:
                card = self.file_cards[file_path]
                card.rebuild()

        # Пересоздаем диалог настроек для новых переводов только если он не должен остаться открытым
        if not keep_settings_open:
            self.settings_dialog = SettingsDialog(
                page=self.page, on_save=self.on_settings_save
            )

            # Загружаем текущие настройки в диалог
            current_settings = self.settings.get_all_settings()
            current_settings["output_mode"] = self.settings.get_output_mode().value
            self.settings_dialog.current_settings = current_settings

        self.update_ui()
        self.page.update()


async def main_async(page: ft.Page):
    """Главная функция приложения"""
    MetadataCleanerApp(page)


def main():
    """Точка входа"""
    ft.app(target=main_async)


if __name__ == "__main__":
    main()
