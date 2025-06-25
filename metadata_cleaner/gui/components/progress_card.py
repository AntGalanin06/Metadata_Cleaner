from __future__ import annotations

import flet as ft

from metadata_cleaner.gui.localization import translator


class ProgressCard(ft.UserControl):
    """Карточка для отображения общего прогресса"""

    def __init__(self):
        super().__init__()
        self.progress_ring = ft.ProgressRing(
            value=0, width=64, height=64, stroke_width=5, visible=True
        )
        self.status_icon = ft.Icon(size=48, visible=False)
        self.status_text = ft.Text(
            translator.get("ready_to_work"),
            weight=ft.FontWeight.BOLD,
            size=18,
            text_align=ft.TextAlign.CENTER,
        )
        self.details_text = ft.Text(
            translator.get("select_files_to_start"),
            size=14,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.ON_SURFACE_VARIANT,
            no_wrap=False,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

    def build(self):
        return ft.Card(
            elevation=2,
            content=ft.Container(
                content=self._build_content(),
                padding=ft.padding.all(16),
                bgcolor=ft.colors.SURFACE_VARIANT,
                border_radius=16,
                expand=True,
            ),
        )

    def _build_content(self):
        """Строит содержимое в зависимости от состояния"""
        # Если есть активная иконка или активный прогресс (больше 0) - показываем с иконкой
        has_active_progress = (
            self.progress_ring.visible and (self.progress_ring.value or 0) > 0
        )
        has_status_icon = self.status_icon.visible

        if has_active_progress or has_status_icon:
            return ft.Row(
                [
                    ft.Stack(
                        [
                            self.progress_ring,
                            self.status_icon,
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Container(
                                content=self.status_text,
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(bottom=4),
                                expand=True,
                            ),
                            ft.Container(
                                content=self.details_text,
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=2),
                                expand=True,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            )
        else:
            # Только текст на всю ширину (начальное состояние)
            return ft.Column(
                [
                    ft.Container(
                        content=self.status_text,
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(bottom=4),
                    ),
                    ft.Container(
                        content=self.details_text,
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=2),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

    def update_progress(self, status: str, details: str, value: float | None = None):
        """Обновление прогресса"""
        self.status_text.value = status
        self.details_text.value = details

        if value is not None:
            self.progress_ring.value = value

        self.status_icon.visible = False
        self.progress_ring.visible = True

        if hasattr(self, "page") and self.page:
            self._rebuild()

    def show_success(self, status: str, details: str):
        """Показать успешное завершение"""
        self.status_text.value = status
        self.details_text.value = details
        self.status_icon.name = ft.icons.CHECK_CIRCLE
        self.status_icon.color = ft.colors.GREEN
        self.status_icon.visible = True
        self.progress_ring.visible = False

        if hasattr(self, "page") and self.page:
            self._rebuild()

    def show_error(self, status: str, details: str):
        """Показать завершение с ошибкой"""
        self.status_text.value = status
        self.details_text.value = details
        self.status_icon.name = ft.icons.ERROR
        self.status_icon.color = ft.colors.RED
        self.status_icon.visible = True
        self.progress_ring.visible = False

        if hasattr(self, "page") and self.page:
            self._rebuild()

    def reset(self):
        """Сброс состояния"""
        self.progress_ring.value = 0
        self.status_text.value = translator.get("ready_to_work")
        self.details_text.value = translator.get("select_files_to_start")
        self.status_icon.visible = False
        self.progress_ring.visible = True

        if hasattr(self, "page") and self.page:
            self._rebuild()

    def _rebuild(self):
        """Перестраивает контент"""
        # Получаем новый контент
        new_content = self._build_content()
        # Обновляем содержимое карточки
        self.controls[0].content.content = new_content
        self.update()

    def rebuild(self):
        """Пересобирает компонент для смены языка"""
        # Обновляем переводы только если в состоянии покоя
        if not self.status_icon.visible and (self.progress_ring.value or 0) == 0:
            self.status_text.value = translator.get("ready_to_work")
            self.details_text.value = translator.get("select_files_to_start")
            if hasattr(self, "page") and self.page:
                self._rebuild()
