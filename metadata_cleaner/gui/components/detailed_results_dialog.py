"""Диалог подробных результатов очистки метаданных."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from metadata_cleaner.gui.localization import translator
from metadata_cleaner.cleaner.metadata_registry import MetadataRegistry

if TYPE_CHECKING:
    from collections.abc import Callable

    from metadata_cleaner.cleaner.models import CleanResult


class DetailedResultsDialog(ft.UserControl):
    """Диалог с подробными результатами очистки метаданных"""

    def __init__(
        self,
        results: dict[str, CleanResult] | None = None,
        on_close: Callable | None = None,
    ):
        super().__init__()
        self.results = results or {}
        self.on_close = on_close
        self.dialog: ft.AlertDialog | None = None

    def build(self):
        return ft.Container()

    def show(self, page: ft.Page):
        """Показать диалог"""
        self.page = page
        self.dialog = ft.AlertDialog(
            title=self._build_title(),
            content=self._build_content(),
            actions=self._build_actions(),
            modal=True,
        )

        page.dialog = self.dialog
        self.dialog.open = True
        page.update()

    def _build_title(self) -> ft.Row:
        """Построить заголовок диалога"""
        return ft.Row(
            [
                ft.Icon(ft.icons.ANALYTICS_OUTLINED, size=24),
                ft.Text(
                    translator.get("detailed_results"),
                    size=20,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=8,
        )

    def _build_content(self) -> ft.Container:
        """Построить содержимое диалога"""
        if not self.results:
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.icons.INFO_OUTLINED,
                            size=48,
                            color=ft.colors.OUTLINE,
                        ),
                        ft.Text(
                            translator.get("no_results_yet"),
                            size=16,
                            color=ft.colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                ),
                width=600,
                height=400,
                alignment=ft.alignment.center,
            )

        # Создаем список результатов
        results_list = ft.ListView(
            height=500,
            width=800,
            spacing=8,
            padding=ft.padding.all(16),
        )

        # Статистика
        total_files = len(self.results)
        successful_files = sum(1 for r in self.results.values() if r.is_success)
        failed_files = total_files - successful_files

        # Заголовок со статистикой
        stats_header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                str(total_files),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.PRIMARY,
                            ),
                            ft.Text(
                                translator.get("total_files"),
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                str(successful_files),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREEN,
                            ),
                            ft.Text(
                                translator.get("successful"),
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                str(failed_files),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=(
                                    ft.colors.RED
                                    if failed_files > 0
                                    else ft.colors.ON_SURFACE_VARIANT
                                ),
                            ),
                            ft.Text(
                                translator.get("failed"),
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            padding=ft.padding.all(16),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=12,
            margin=ft.margin.only(bottom=16),
        )

        results_list.controls.append(stats_header)

        # Добавляем результаты для каждого файла
        for result in self.results.values():
            results_list.controls.append(self._build_file_result_card(result))

        return ft.Container(
            content=results_list,
            width=800,
            height=500,
        )

    def _build_file_result_card(self, result: CleanResult) -> ft.Card:
        """Построить карточку результата для файла"""
        path = result.job.file_path

        if result.is_success:
            # Успешная обработка
            status_icon = ft.Icon(
                ft.icons.CHECK_CIRCLE,
                color=ft.colors.GREEN,
                size=24,
            )

            # Информация об очищенных метаданных
            cleaned_count = len(result.cleaned_fields or {})
            if cleaned_count > 0:
                status_text = translator.get(
                    "metadata_cleaned_count", count=cleaned_count
                )
                metadata_chips = []

                if result.cleaned_fields:
                    # Определяем тип файла для правильного маппинга
                    file_type = self._get_file_type_from_path(result.job.file_path)

                    # Получаем маппинг полей результата на настройки метаданных
                    field_mapping = MetadataRegistry.map_result_fields_to_metadata(
                        file_type, result.cleaned_fields
                    )

                    # Создаем красивые теги для групп метаданных
                    for metadata_key in field_mapping:
                        field_info = MetadataRegistry.get_field_by_key(
                            file_type, metadata_key
                        )
                        if field_info:
                            # Используем человекочитаемое название из переводчика
                            display_name = translator.get(field_info.name_key)
                            category_color, category_icon = self._get_category_style(
                                field_info.category
                            )

                            metadata_chips.append(
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                category_icon,
                                                size=14,
                                                color=category_color,
                                            ),
                                            ft.Text(
                                                display_name,
                                                size=11,
                                                weight=ft.FontWeight.W_500,
                                                color=category_color,
                                            ),
                                        ],
                                        spacing=4,
                                        tight=True,
                                    ),
                                    padding=ft.padding.symmetric(
                                        horizontal=8, vertical=4
                                    ),
                                    bgcolor=f"{category_color}0F",  # 6% opacity
                                    border=ft.border.all(
                                        1, f"{category_color}3D"
                                    ),  # 24% opacity
                                    border_radius=16,
                                    tooltip=translator.get(field_info.description_key),
                                )
                            )

                    # Добавляем необработанные поля если они есть
                    processed_fields = set()
                    for fields in field_mapping.values():
                        processed_fields.update(fields)

                    for field in result.cleaned_fields:
                        if field not in processed_fields:
                            metadata_chips.append(
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                ft.icons.LABEL_OUTLINE,
                                                size=14,
                                                color=ft.colors.BLUE_700,
                                            ),
                                            ft.Text(
                                                self._format_field_name(field),
                                                size=11,
                                                weight=ft.FontWeight.W_500,
                                                color=ft.colors.BLUE_700,
                                            ),
                                        ],
                                        spacing=4,
                                        tight=True,
                                    ),
                                    padding=ft.padding.symmetric(
                                        horizontal=8, vertical=4
                                    ),
                                    bgcolor=f"{ft.colors.BLUE_700}0F",  # 6% opacity
                                    border=ft.border.all(
                                        1, f"{ft.colors.BLUE_700}3D"
                                    ),  # 24% opacity
                                    border_radius=16,
                                    tooltip=f"Очищено поле: {self._format_field_name(field)} ({field})",
                                )
                            )

                # Создаем секцию для отображения всех очищенных метаданных
                metadata_section = ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.CLEANING_SERVICES,
                                    size=16,
                                    color=ft.colors.GREEN_700,
                                ),
                                ft.Text(
                                    translator.get("cleaned_metadata"),
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.colors.GREEN_700,
                                ),
                            ],
                            spacing=6,
                        ),
                        ft.Container(
                            content=ft.Row(
                                metadata_chips,  # Показываем ВСЕ очищенные метаданные с красивыми названиями
                                wrap=True,
                                spacing=6,
                                run_spacing=6,
                            ),
                            padding=ft.padding.only(left=22),  # Отступ под иконку
                        ),
                    ],
                    spacing=8,
                )
            else:
                status_text = translator.get("no_metadata_found")
                metadata_section = ft.Row(
                    [
                        ft.Icon(
                            ft.icons.INFO_OUTLINE,
                            size=16,
                            color=ft.colors.ORANGE_700,
                        ),
                        ft.Text(
                            translator.get("file_had_no_metadata"),
                            size=12,
                            color=ft.colors.ON_SURFACE_VARIANT,
                            italic=True,
                            weight=ft.FontWeight.W_400,
                        ),
                    ],
                    spacing=6,
                )
        else:
            # Ошибка обработки
            status_icon = ft.Icon(
                ft.icons.ERROR,
                color=ft.colors.RED,
                size=24,
            )
            status_text = translator.get("processing_failed")
            metadata_section = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.icons.ERROR_OUTLINE,
                            size=16,
                            color=ft.colors.RED_700,
                        ),
                        ft.Text(
                            result.message or translator.get("unknown_error"),
                            size=12,
                            color=ft.colors.RED_700,
                            italic=True,
                        ),
                    ],
                    spacing=6,
                ),
                padding=ft.padding.all(8),
                bgcolor=ft.colors.RED_50,
                border=ft.border.all(1, ft.colors.RED_200),
                border_radius=8,
            )

        # Информация о времени обработки
        processing_time = getattr(result, "processing_time", 0.0)
        time_text = ft.Text(
            translator.get("processing_time", time=f"{processing_time:.2f}s"),
            size=10,
            color=ft.colors.ON_SURFACE_VARIANT,
        )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                status_icon,
                                ft.Column(
                                    [
                                        ft.Text(
                                            path.name,
                                            size=14,
                                            weight=ft.FontWeight.W_500,
                                        ),
                                        ft.Text(
                                            status_text,
                                            size=12,
                                            color=ft.colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                time_text,
                            ],
                            spacing=12,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        metadata_section,
                    ],
                    spacing=12,
                ),
                padding=ft.padding.all(16),
            ),
            elevation=2,
            margin=ft.margin.only(bottom=8),
        )

    def _build_actions(self) -> list[ft.Control]:
        """Построить кнопки действий"""
        return [
            ft.TextButton(
                translator.get("close"),
                on_click=self._close_dialog,
                icon=ft.icons.CLOSE,
            ),
        ]

    def _close_dialog(self, e):
        """Закрыть диалог"""
        if self.dialog:
            self.dialog.open = False
            if hasattr(self, "page") and self.page:
                self.page.update()
        if self.on_close:
            self.on_close()

    def update_results(self, results: dict[str, CleanResult]):
        """Обновить результаты"""
        self.results = results
        if self.dialog and self.dialog.open:
            self.dialog.content = self._build_content()
            if hasattr(self, "page") and self.page:
                self.page.update()

    def _get_file_type_from_path(self, file_path) -> str:
        """Определить тип файла по расширению."""
        extension = file_path.suffix.lower()

        if extension in [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".heic",
            ".heif",
            ".tiff",
            ".tif",
        ]:
            return "image"
        elif extension in [".docx", ".pptx"]:
            return "document"
        elif extension == ".pdf":
            return "pdf"
        elif extension in [".mp4", ".mov", ".avi", ".mkv"]:
            return "video"
        elif extension in [".xlsx", ".xls"]:
            return "document"  # Используем те же настройки что и для документов
        else:
            return "unknown"

    def _get_category_style(self, category) -> tuple[str, str]:
        """Получить цвет и иконку для категории метаданных."""
        from metadata_cleaner.cleaner.metadata_registry import (
            MetadataCategory,
        )  # noqa: PLC0415

        category_styles = {
            MetadataCategory.AUTHOR: (ft.colors.PURPLE_700, ft.icons.PERSON),
            MetadataCategory.DATETIME: (ft.colors.ORANGE_700, ft.icons.ACCESS_TIME),
            MetadataCategory.LOCATION: (ft.colors.BLUE_700, ft.icons.LOCATION_ON),
            MetadataCategory.CAMERA: (ft.colors.GREEN_700, ft.icons.CAMERA_ALT),
            MetadataCategory.TECHNICAL: (ft.colors.INDIGO_700, ft.icons.SETTINGS),
            MetadataCategory.CONTENT: (ft.colors.TEAL_700, ft.icons.DESCRIPTION),
        }

        return category_styles.get(category, (ft.colors.BLUE_GREY_700, ft.icons.LABEL))

    def _format_field_name(self, field_name: str) -> str:
        """Преобразовать техническое название поля в читаемое."""
        # Словарь для перевода технических названий в человеко-читаемые
        field_translations = {
            # Общие поля
            "artist": "Автор",
            "author": "Автор",
            "author_info": "Информация об авторе",
            "camera_owner": "Владелец камеры",
            "creator": "Создатель",
            "copyright": "Авторские права",
            # Временные метки
            "date_original": "Дата съемки",
            "date_digitized": "Дата оцифровки",
            "created": "Дата создания",
            "modified": "Дата изменения",
            "last_printed": "Дата печати",
            "creation_info": "Информация о создании",
            # Устройство и камера
            "camera_make": "Производитель камеры",
            "camera_model": "Модель камеры",
            "software": "ПО",
            "body_serial": "Серийный номер корпуса",
            "lens_serial": "Серийный номер объектива",
            # Геолокация
            "gps_data": "GPS данные",
            "gps_info": "Информация GPS",
            # Комментарии и описания
            "user_comment": "Комментарий пользователя",
            "comments": "Комментарии",
            "comment_info": "Информация комментариев",
            "title": "Заголовок",
            "title_info": "Информация заголовка",
            "subject": "Тема",
            "keywords": "Ключевые слова",
            # Документы
            "last_modified_by": "Последний редактор",
            "last_modified_by_alt": "Редактор (альт.)",
            "company": "Компания",
            "revision": "Версия",
            "version": "Номер версии",
            "content_status": "Статус содержимого",
            "category": "Категория",
            "language": "Язык",
            "identifier": "Идентификатор",
            # PDF
            "producer": "Производитель PDF",
            # Видео
            "method": "Метод кодирования",
            # Специфичные для форматов
            "gif_version": "Версия GIF",
            "png_title": "Заголовок PNG",
            "png_author": "Автор PNG",
        }

        # Возвращаем переведенное название или форматированное техническое
        if field_name in field_translations:
            return field_translations[field_name]
        else:
            # Для неизвестных полей делаем читаемое форматирование
            # Заменяем подчеркивания на пробелы и делаем первую букву заглавной
            formatted = field_name.replace("_", " ").title()
            return formatted
