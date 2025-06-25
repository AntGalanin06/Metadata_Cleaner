from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import flet as ft

from metadata_cleaner.cleaner.models import CleanResult, CleanStatus
from metadata_cleaner.gui.localization import translator

if TYPE_CHECKING:
    from collections.abc import Callable


class FileCard(ft.UserControl):
    """Карточка для отображения информации о файле"""

    def __init__(self, file_path: str, on_remove: Callable[[FileCard], None]):
        super().__init__()
        self.file_path = file_path
        self.on_remove = on_remove

        # Устанавливаем атрибуты из пути
        path = Path(file_path)
        self.file_name = path.name

        # Безопасное получение размера файла
        try:
            self.file_size = path.stat().st_size
        except (OSError, FileNotFoundError):
            self.file_size = 0

        self.file_type_icon = self._get_file_icon()
        self.cleaning_result: CleanResult | None = None
        self.is_processing = False

        # Создаем кнопку удаления один раз
        self.remove_button = ft.IconButton(
            icon=ft.icons.CLOSE,
            icon_size=16,
            icon_color=ft.colors.RED,
            tooltip=translator.get("remove_from_list"),
            on_click=lambda e: self.on_remove(self),
        )

    def build(self):
        return self._build_content()

    def rebuild(self):
        """Пересобирает контент карточки (для смены языка)"""
        # Обновляем tooltip кнопки
        self.remove_button.tooltip = translator.get("remove_from_list")
        if hasattr(self, "page") and self.page:
            self.update()

    def _get_file_icon(self) -> ft.Icon:
        """Получение иконки в зависимости от типа файла"""
        ext = Path(self.file_path).suffix.lower()
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

    def _build_content(self) -> ft.Card:
        """Построение содержимого карточки"""
        # Статус обработки
        if self.is_processing:
            status_text = translator.get("status_processing")
            status_color = ft.colors.ORANGE
            status_icon = ft.Icon(
                ft.icons.HOURGLASS_EMPTY, color=ft.colors.ORANGE, size=16
            )
        elif self.cleaning_result:
            if self.cleaning_result.status == CleanStatus.ERROR:
                status_text = translator.get("status_error")
                status_color = ft.colors.RED
                status_icon = ft.Icon(ft.icons.ERROR, color=ft.colors.RED, size=16)
            else:
                status_text = translator.get("status_success")
                status_color = ft.colors.GREEN
                status_icon = ft.Icon(
                    ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=16
                )
        else:
            status_text = translator.get("status_pending")
            status_color = ft.colors.ON_SURFACE_VARIANT
            status_icon = ft.Icon(
                ft.icons.SCHEDULE, color=ft.colors.ON_SURFACE_VARIANT, size=16
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        # Верхняя часть с иконкой и информацией
                        ft.Row(
                            [
                                self.file_type_icon,
                                ft.Column(
                                    [
                                        ft.Text(
                                            self.file_name,
                                            size=14,
                                            weight=ft.FontWeight.W_500,
                                            color=ft.colors.ON_SURFACE,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            str(
                                                Path(self.file_path).parent.name
                                            ),  # Только имя папки
                                            size=11,
                                            weight=ft.FontWeight.W_400,
                                            color=ft.colors.ON_SURFACE_VARIANT,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            f"{self.file_size / 1024:.2f} KB",
                                            size=11,
                                            color=ft.colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Divider(height=1),
                        # Нижняя часть со статусом и кнопкой удаления
                        ft.Row(
                            [
                                status_icon,
                                ft.Text(
                                    status_text,
                                    color=status_color,
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Container(expand=True),
                                self.remove_button,  # Используем сохраненную кнопку
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=6,
                ),
                padding=ft.padding.all(10),
            ),
            elevation=2,
            margin=ft.margin.all(2),
        )

    def set_processing_status(self):
        """Установка статуса обработки"""
        self.is_processing = True
        self.cleaning_result = None
        self.update()

    def update_cleaning_result(self, result: CleanResult):
        """Обновление результата очистки"""
        self.is_processing = False
        self.cleaning_result = result
        self.update()

    def update(self):
        """Обновление карточки"""
        if hasattr(self, "page") and self.page:
            # Перестраиваем содержимое
            new_content = self._build_content()
            # Копируем содержимое в текущую карточку
            if hasattr(self, "controls") and len(self.controls) > 0:
                self.controls[0] = new_content
            else:
                self.controls = [new_content]
            super().update()
