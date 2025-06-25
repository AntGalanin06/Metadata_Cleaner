from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from metadata_cleaner.gui.localization import translator

if TYPE_CHECKING:
    from collections.abc import Callable


class ActionBar(ft.UserControl):
    """Панель действий с кнопками"""

    def __init__(
        self,
        on_pick_files: Callable | None = None,
        on_pick_folder: Callable | None = None,
        on_clear_list: Callable | None = None,
        on_clean_metadata: Callable | None = None,
        on_toggle_theme: Callable | None = None,
        on_show_settings: Callable | None = None,
    ):
        super().__init__()
        self.on_pick_files = on_pick_files
        self.on_pick_folder = on_pick_folder
        self.on_clear_list = on_clear_list
        self.on_clean_metadata = on_clean_metadata
        self.on_toggle_theme = on_toggle_theme
        self.on_show_settings = on_show_settings

        self.is_processing = False
        self.clean_enabled = False

        # Создаем кнопки как атрибуты
        self.pick_files_btn = ft.ElevatedButton(
            text=translator.get("pick_files"),
            icon=ft.icons.FILE_UPLOAD_OUTLINED,
            on_click=self.on_pick_files,
        )

        self.pick_folder_btn = ft.ElevatedButton(
            text=translator.get("pick_folder"),
            icon=ft.icons.FOLDER_OUTLINED,
            on_click=self.on_pick_folder,
        )

        self.clear_list_btn = ft.ElevatedButton(
            text=translator.get("clear"),
            icon=ft.icons.CLEAR_ALL,
            on_click=self.on_clear_list,
            disabled=True,
        )

        self.clean_btn = ft.ElevatedButton(
            text=translator.get("clean_metadata"),
            icon=ft.icons.CLEANING_SERVICES,
            on_click=self.on_clean_metadata,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.PRIMARY,
                color=ft.colors.ON_PRIMARY,
            ),
            disabled=True,
        )

    def build(self):
        return ft.Row(
            [
                self.pick_files_btn,
                self.pick_folder_btn,
                self.clear_list_btn,
                ft.Container(expand=True),
                self.clean_btn,
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
        )

    def set_processing_state(self, is_processing: bool):
        """Установка состояния обработки"""
        self.is_processing = is_processing
        self.pick_files_btn.disabled = is_processing
        self.pick_folder_btn.disabled = is_processing
        self.clear_list_btn.disabled = is_processing

        if is_processing:
            self.clean_btn.text = translator.get("processing")
            self.clean_btn.icon = ft.icons.HOURGLASS_EMPTY
            self.clean_btn.disabled = True
        else:
            self.clean_btn.text = translator.get("clean_metadata")
            self.clean_btn.icon = ft.icons.CLEANING_SERVICES
            # Восстанавливаем состояние кнопки на основе clean_enabled
            self.clean_btn.disabled = not self.clean_enabled

        if hasattr(self, "page") and self.page:
            self.update()

    def set_clean_enabled(self, enabled: bool):
        """Установка доступности кнопки очистки"""
        self.clean_enabled = enabled
        if not self.is_processing:
            self.clean_btn.disabled = not enabled
            if hasattr(self, "page") and self.page:
                self.update()

    def show_success_animation(self):
        """Показать анимацию успеха"""
        import threading

        original_text = self.clean_btn.text
        original_icon = self.clean_btn.icon
        original_style = self.clean_btn.style

        # Временно показываем успех
        self.clean_btn.text = translator.get("done")
        self.clean_btn.icon = ft.icons.CHECK
        self.clean_btn.style = ft.ButtonStyle(
            bgcolor=ft.colors.GREEN,
            color=ft.colors.ON_PRIMARY,
        )
        self.clean_btn.disabled = True
        if hasattr(self, "page") and self.page:
            self.update()

        # Возвращаем через 3 секунды
        def restore_button():
            self.clean_btn.text = original_text
            self.clean_btn.icon = original_icon
            self.clean_btn.style = original_style
            self.clean_btn.disabled = not self.clean_enabled
            if hasattr(self, "page") and self.page:
                self.update()

        threading.Timer(3.0, restore_button).start()

    def pulse_animation(self, button: ft.ElevatedButton):
        """Анимация пульсации для кнопки"""
        # Увеличение elevation
        button.style.elevation = {"": 8, "hovered": 12}
        if hasattr(self, "page") and self.page:
            self.update()

        # Возврат к нормальному состоянию
        # Можно добавить таймер

    def update_button_state(self, has_files: bool):
        self.clear_list_btn.disabled = not has_files
        if hasattr(self, "page") and self.page:
            self.update()

    def rebuild(self):
        """Пересобирает компонент для смены языка"""
        self.pick_files_btn.text = translator.get("pick_files")
        self.pick_folder_btn.text = translator.get("pick_folder")
        self.clear_list_btn.text = translator.get("clear")
        self.clean_btn.text = translator.get("clean_metadata")
        if hasattr(self, "page") and self.page:
            self.update()
