from __future__ import annotations

import flet as ft

from metadata_cleaner.gui.localization import translator


class StatsPanel(ft.UserControl):
    """Панель для отображения статистики"""

    def __init__(self):
        self.total_files = 0
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0

        # Элементы UI
        self.total_files_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD)
        self.processed_files_text = ft.Text(
            "0", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE
        )
        self.successful_files_text = ft.Text(
            "0", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN
        )
        self.failed_files_text = ft.Text(
            "0", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.RED
        )
        self.progress_bar = ft.ProgressBar(
            value=0,
            height=8,
            color=ft.colors.PRIMARY,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        # Заголовки
        self.total_label = ft.Text(
            translator.get("total"), size=12, color=ft.colors.ON_SURFACE_VARIANT
        )
        self.processed_label = ft.Text(
            translator.get("processed"), size=12, color=ft.colors.ON_SURFACE_VARIANT
        )
        self.successful_label = ft.Text(
            translator.get("successful"), size=12, color=ft.colors.ON_SURFACE_VARIANT
        )
        self.failed_label = ft.Text(
            translator.get("errors"), size=12, color=ft.colors.ON_SURFACE_VARIANT
        )
        self.progress_label = ft.Text(
            translator.get("progress"), size=12, weight=ft.FontWeight.BOLD
        )
        self.title_label = ft.Text(
            translator.get("statistics"), size=16, weight=ft.FontWeight.W_600
        )

        super().__init__()

    def build(self):
        self.progress_text = ft.Text(
            f"{(self.progress_bar.value or 0) * 100:.0f}%",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.PRIMARY,
        )

        return ft.Card(
            elevation=2,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                self.title_label,
                                ft.Icon(
                                    ft.icons.INSIGHTS, size=20, color=ft.colors.PRIMARY
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=10),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.icons.FOLDER_OUTLINED, size=20
                                                ),
                                                self.total_files_text,
                                            ],
                                            spacing=8,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                        ),
                                        self.total_label,
                                    ],
                                    spacing=4,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.icons.CHECK_CIRCLE_OUTLINE,
                                                    color=ft.colors.GREEN,
                                                    size=20,
                                                ),
                                                self.successful_files_text,
                                            ],
                                            spacing=8,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                        ),
                                        self.successful_label,
                                    ],
                                    spacing=4,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.icons.ERROR_OUTLINE,
                                                    color=ft.colors.RED,
                                                    size=20,
                                                ),
                                                self.failed_files_text,
                                            ],
                                            spacing=8,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                        ),
                                        self.failed_label,
                                    ],
                                    spacing=4,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        ),
                        ft.Divider(height=20),
                        ft.Row(
                            [
                                self.progress_label,
                                self.progress_text,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.progress_bar,
                    ],
                    spacing=8,
                ),
                padding=ft.padding.all(16),
            ),
        )

    def update_stats(self, total: int, processed: int, successful: int, failed: int):
        """Обновление статистики"""
        self.total_files = total
        self.processed_files = processed
        self.successful_files = successful
        self.failed_files = failed

        # Обновление значений
        self.total_files_text.value = str(total)
        self.processed_files_text.value = str(processed)
        self.successful_files_text.value = str(successful)
        self.failed_files_text.value = str(failed)

        # Обновление прогресса
        if total > 0:
            self.progress_bar.value = processed / total
        else:
            self.progress_bar.value = 0

        # Обновление текста с процентами
        if hasattr(self, "progress_text"):
            self.progress_text.value = f"{(self.progress_bar.value or 0) * 100:.0f}%"

        # Обновляем только если компонент добавлен в страницу
        if hasattr(self, "page") and self.page:
            self.update()

    def reset_stats(self):
        """Сброс статистики"""
        self.update_stats(0, 0, 0, 0)
        self.progress_bar.color = ft.colors.PRIMARY

    def animate_update(self):
        """Анимация обновления"""
        # Добавление пульсации для активного обновления
        for stat in [
            self.total_files_text,
            self.processed_files_text,
            self.successful_files_text,
            self.failed_files_text,
        ]:
            stat.style.update(color=ft.colors.PRIMARY)
            stat.style.update(weight=ft.FontWeight.W_500)

        self.update()

        # Возврат к нормальному цвету
        def reset_colors():
            for stat in [
                self.total_files_text,
                self.processed_files_text,
                self.successful_files_text,
                self.failed_files_text,
            ]:
                stat.style.update(color=ft.colors.ON_SURFACE_VARIANT)
                stat.style.update(weight=ft.FontWeight.W_400)
            self.update()

        # Можно добавить таймер для сброса цветов

    def rebuild(self):
        """Пересобирает компонент для смены языка"""
        self.total_label.value = translator.get("total")
        self.processed_label.value = translator.get("processed")
        self.successful_label.value = translator.get("successful")
        self.failed_label.value = translator.get("errors")
        self.progress_label.value = translator.get("progress")
        self.title_label.value = translator.get("statistics")
        if hasattr(self, "page") and self.page:
            self.update()
