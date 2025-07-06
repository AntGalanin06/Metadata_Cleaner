"""Диалог подробных результатов очистки метаданных."""

from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from metadata_cleaner.gui.localization import translator

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
        self.dialog = None

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
                                color=ft.colors.RED if failed_files > 0 else ft.colors.ON_SURFACE_VARIANT,
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
        for file_path, result in self.results.items():
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
                status_text = translator.get("metadata_cleaned_count", count=cleaned_count)
                metadata_chips = []
                if result.cleaned_fields:
                    for field in result.cleaned_fields.keys():
                        metadata_chips.append(
                            ft.Chip(
                                label=ft.Text(field, size=10),
                                bgcolor=ft.colors.GREEN_100,
                                selected_color=ft.colors.GREEN,
                            )
                        )
                
                # Создаем секцию для отображения всех очищенных метаданных
                metadata_section = ft.Column(
                    [
                        ft.Text(
                            translator.get("cleaned_metadata"),
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=ft.colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Row(
                            metadata_chips,  # Показываем ВСЕ очищенные метаданные
                            wrap=True,
                            spacing=4,
                        ),
                    ],
                    spacing=8,
                )
            else:
                status_text = translator.get("no_metadata_found")
                metadata_section = ft.Text(
                    translator.get("file_had_no_metadata"),
                    size=12,
                    color=ft.colors.ON_SURFACE_VARIANT,
                    italic=True,
                )
        else:
            # Ошибка обработки
            status_icon = ft.Icon(
                ft.icons.ERROR,
                color=ft.colors.RED,
                size=24,
            )
            status_text = translator.get("processing_failed")
            metadata_section = ft.Text(
                result.message or translator.get("unknown_error"),
                size=12,
                color=ft.colors.RED,
                italic=True,
            )

        # Информация о времени обработки
        processing_time = getattr(result, 'processing_time', 0.0)
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