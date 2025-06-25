from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from metadata_cleaner.gui.localization import translator

if TYPE_CHECKING:
    from collections.abc import Callable


class SettingsDialog(ft.UserControl):
    """Диалог настроек приложения"""

    def __init__(
        self,
        page: ft.Page,
        on_save: Callable | None = None,
    ):
        super().__init__()
        self.page = page
        self.on_save = on_save
        self.dialog = None
        self.current_tab_index = 0  # Индекс активной вкладки

        # Текущие настройки
        self.current_settings = {
            "theme": "system",
            "output_mode": "create_copy",
            "create_backup": True,
            "language": "ru",
            "file_type_settings": {
                "image": {
                    # EXIF данные
                    "exif_author": True,        # Автор фотографии
                    "exif_copyright": True,     # Авторские права
                    "exif_datetime": True,      # Дата и время съемки
                    "exif_camera": True,        # Модель камеры и настройки
                    "exif_software": True,      # ПО для обработки
                    # GPS данные
                    "gps_coords": True,         # GPS координаты
                    "gps_altitude": True,       # Высота над уровнем моря
                    # Персональные данные
                    "camera_owner": True,       # Владелец камеры
                    "camera_serial": True,      # Серийный номер камеры
                    "user_comments": True,      # Комментарии пользователя
                },
                "document": {
                    # Авторские данные
                    "author": True,             # Автор документа
                    "last_modified_by": True,   # Последний редактор
                    "company": True,            # Компания
                    # Временные данные
                    "created": True,            # Дата создания
                    "modified": True,           # Дата изменения
                    "last_printed": True,       # Дата последней печати
                    # Документооборот
                    "revision": True,           # Номер ревизии
                    "version": True,            # Версия документа
                    "content_status": True,     # Статус контента
                    "category": True,           # Категория
                    "language": True,           # Язык документа
                    "identifier": True,         # Уникальный идентификатор
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Заголовок
                    "subject": False,           # Тема
                    "keywords": False,          # Ключевые слова
                    "comments": False,          # Комментарии к содержанию
                },
                "pdf": {
                    # Авторские данные
                    "author": True,             # Автор PDF
                    "creator": True,            # Создатель (программа)
                    "producer": True,           # Производитель PDF
                    # Временные данные
                    "created": True,            # Дата создания
                    "modified": True,           # Дата изменения
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Заголовок документа
                    "subject": False,           # Тема документа
                    "keywords": False,          # Ключевые слова
                },
                "video": {
                    # Авторские данные
                    "author": True,             # Автор/создатель видео
                    "encoder": True,            # Энкодер/программа записи
                    # Временные данные
                    "creation_time": True,      # Дата и время создания
                    # GPS и локация
                    "gps_coords": True,         # GPS координаты
                    "location": True,           # Информация о местоположении
                    # Техническая информация
                    "major_brand": True,        # Основной бренд контейнера
                    "compatible_brands": True,  # Совместимые форматы
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Название видео
                    "comment": False,           # Комментарии/описание
                    "description": False,       # Подробное описание
                },
            },
        }

    def build(self):
        return ft.Container()

    def update_settings(self, settings: dict):
        """Обновить настройки диалога"""
        self.current_settings = settings.copy()

        # Обновляем UI если диалог открыт
        if self.dialog and self.dialog.open:
            self.dialog.content = self._build_content()
            self.page.update()

    def show(self):
        """Показать диалог настроек"""
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.icons.SETTINGS, size=24),
                    ft.Text(
                        translator.get("settings"), size=20, weight=ft.FontWeight.W_600
                    ),
                ],
                spacing=8,
            ),
            content=self._build_content(),
            actions=[
                ft.TextButton(
                    translator.get("cancel"),
                    on_click=self._cancel,
                    style=ft.ButtonStyle(
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                ),
                ft.TextButton(
                    translator.get("reset_defaults"),
                    on_click=self._reset_defaults,
                    style=ft.ButtonStyle(
                        color=ft.colors.PRIMARY,
                    ),
                ),
                ft.FilledButton(
                    translator.get("save"),
                    icon=ft.icons.SAVE,
                    on_click=self._save_settings,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def _build_content(self) -> ft.Container:
        """Построение содержимого диалога"""
        # Создаем вкладки
        tabs = ft.Tabs(
            selected_index=self.current_tab_index,
            animation_duration=300,
            on_change=self._on_tab_change,
            tabs=[
                ft.Tab(
                    text=translator.get("general"),
                    icon=ft.icons.TUNE,
                    content=self._build_general_tab(),
                ),
                ft.Tab(
                    text=translator.get("images"),
                    icon=ft.icons.IMAGE,
                    content=self._build_metadata_tab("image"),
                ),
                ft.Tab(
                    text=translator.get("documents"),
                    icon=ft.icons.DESCRIPTION,
                    content=self._build_metadata_tab("document"),
                ),
                ft.Tab(
                    text=translator.get("pdf"),
                    icon=ft.icons.PICTURE_AS_PDF,
                    content=self._build_metadata_tab("pdf"),
                ),
                ft.Tab(
                    text=translator.get("video"),
                    icon=ft.icons.VIDEOCAM,
                    content=self._build_metadata_tab("video"),
                ),
                ft.Tab(
                    text=translator.get("about"),
                    icon=ft.icons.INFO,
                    content=self._build_about_tab(),
                ),
            ],
            expand=1,
        )

        return ft.Container(
            content=tabs,
            width=900,
            height=600,
            padding=ft.padding.all(0),
        )

    def _on_tab_change(self, e):
        """Обработчик изменения вкладки"""
        self.current_tab_index = e.control.selected_index

    def _build_general_tab(self) -> ft.Container:
        """Вкладка общих настроек"""
        self.theme_dropdown = ft.Dropdown(
            label=translator.get("theme"),
            options=[
                ft.dropdown.Option("system", translator.get("system_theme")),
                ft.dropdown.Option("light", translator.get("light_theme")),
                ft.dropdown.Option("dark", translator.get("dark_theme")),
            ],
            value=self.current_settings["theme"],
            width=200,
        )

        self.output_mode_dropdown = ft.Dropdown(
            label=translator.get("output_mode"),
            options=[
                ft.dropdown.Option("create_copy", translator.get("create_copy")),
                ft.dropdown.Option("replace", translator.get("overwrite")),
                ft.dropdown.Option(
                    "backup_and_overwrite", translator.get("backup_and_overwrite")
                ),
            ],
            value=self.current_settings["output_mode"],
            width=250,
        )

        self.language_dropdown = ft.Dropdown(
            label=translator.get("language"),
            options=[
                ft.dropdown.Option("ru", translator.get("russian")),
                ft.dropdown.Option("en", translator.get("english")),
            ],
            value=self.current_settings.get("language", "ru"),
            width=150,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        translator.get("main_settings"),
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(),
                    ft.Row(
                        [
                            self.theme_dropdown,
                            self.language_dropdown,
                        ],
                        spacing=20,
                    ),
                    ft.Text(
                        translator.get("file_processing"),
                        size=16,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Container(height=8),
                    self.output_mode_dropdown,
                    ft.Container(height=8),
                    ft.Text(
                        translator.get("info"), size=14, weight=ft.FontWeight.W_500
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                translator.get("info_create_copy"),
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                translator.get("info_overwrite"),
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                translator.get("info_backup_overwrite"),
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.all(20),
        )

    def _get_card_colors(self, is_enabled: bool) -> tuple[str, str]:
        """Получить цвета для карточки в зависимости от темы"""
        # Определяем, темная ли тема
        is_dark_theme = False
        if hasattr(self.page, 'theme_mode'):
            if self.page.theme_mode == ft.ThemeMode.DARK:
                is_dark_theme = True
            elif self.page.theme_mode == ft.ThemeMode.LIGHT:
                is_dark_theme = False
            else:  # SYSTEM
                # Пытаемся определить системную тему
                if hasattr(self.page, 'platform_brightness'):
                    is_dark_theme = self.page.platform_brightness == ft.Brightness.DARK
        
        if is_dark_theme:
            # Для темной темы используем более контрастные цвета
            if is_enabled:
                return ft.colors.RED_900, ft.colors.RED_200  # bgcolor, text_color
            else:
                return ft.colors.GREEN_900, ft.colors.GREEN_200
        else:
            # Для светлой темы используем оригинальные цвета
            if is_enabled:
                return ft.colors.RED_50, ft.colors.ON_SURFACE
            else:
                return ft.colors.GREEN_50, ft.colors.ON_SURFACE

    def _build_metadata_tab(self, file_type: str) -> ft.Container:
        """Вкладка настроек метаданных для типа файла"""
        settings = self.current_settings["file_type_settings"][file_type]

        # Определяем доступные поля для каждого типа (все реальные метаданные)
        fields_config = {
            "image": [
                # EXIF данные
                ("exif_author", "exif_author", "exif_author_desc"),
                ("exif_copyright", "exif_copyright", "exif_copyright_desc"),
                ("exif_datetime", "exif_datetime", "exif_datetime_desc"),
                ("exif_camera", "exif_camera", "exif_camera_desc"),
                ("exif_software", "exif_software", "exif_software_desc"),
                # GPS данные  
                ("gps_coords", "gps_coords", "gps_coords_desc"),
                ("gps_altitude", "gps_altitude", "gps_altitude_desc"),
                # Персональные данные
                ("camera_owner", "camera_owner", "camera_owner_desc"),
                ("camera_serial", "camera_serial", "camera_serial_desc"),
                ("user_comments", "user_comments", "user_comments_desc"),
            ],
            "document": [
                # Авторские данные
                ("author", "author", "author_desc"),
                ("last_modified_by", "last_modified_by", "last_modified_by_desc"),
                ("company", "company", "company_desc"),
                # Временные данные
                ("created", "created", "created_desc"),
                ("modified", "modified", "modified_desc"),
                ("last_printed", "last_printed", "last_printed_desc"),
                # Документооборот
                ("revision", "revision", "revision_desc"),
                ("version", "version", "version_desc"),
                ("content_status", "content_status", "content_status_desc"),
                ("category", "category", "category_desc"),
                ("language", "language", "language_desc"),
                ("identifier", "identifier", "identifier_desc"),
                # Контент (по умолчанию НЕ удаляем)
                ("title", "title", "title_desc"),
                ("subject", "subject", "subject_desc"),
                ("keywords", "keywords", "keywords_desc"),
                ("comments", "comments", "comments_desc"),
            ],
            "pdf": [
                # Авторские данные
                ("author", "author", "author_desc"),
                ("creator", "creator", "creator_desc"),
                ("producer", "producer", "producer_desc"),
                # Временные данные
                ("created", "created", "created_desc"),
                ("modified", "modified", "modified_desc"),
                # Контент (по умолчанию НЕ удаляем)
                ("title", "title", "title_desc"),
                ("subject", "subject", "subject_desc"),
                ("keywords", "keywords", "keywords_desc"),
            ],
            "video": [
                # Авторские данные
                ("author", "author", "author_desc"),
                ("encoder", "encoder", "encoder_desc"),
                # Временные данные
                ("creation_time", "creation_time", "creation_time_desc"),
                # GPS и локация
                ("gps_coords", "gps_coords", "gps_coords_desc"),
                ("location", "location", "location_desc"),
                # Техническая информация
                ("major_brand", "major_brand", "major_brand_desc"),
                ("compatible_brands", "compatible_brands", "compatible_brands_desc"),
                # Контент (по умолчанию НЕ удаляем)
                ("title", "title", "title_desc"),
                ("comment", "comment", "comment_desc"),
                ("description", "description", "description_desc"),
            ],
        }

        fields = fields_config.get(file_type, [])

        # Создаем переключатели для каждого поля
        switches = []
        
        for field_key, field_name_key, field_desc_key in fields:
            field_name = translator.get(field_name_key)
            field_desc = translator.get(field_desc_key)
            
            switch = ft.Switch(
                label=field_name,
                value=settings.get(field_key, True),
                data=field_key,  # Сохраняем ключ для обновления
                on_change=lambda e, file_type=file_type, field_key=field_key: self._on_metadata_switch_change(e, file_type, field_key),
            )

            # Определяем цвет карточки по умолчанию (красный для удаляемых, зеленый для сохраняемых)
            is_enabled = settings.get(field_key, True)
            card_color, text_color = self._get_card_colors(is_enabled)
            
            switches.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        switch,
                                    ]
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        field_desc,
                                        size=12,
                                        color=text_color if text_color != ft.colors.ON_SURFACE else ft.colors.ON_SURFACE_VARIANT,
                                    ),
                                    padding=ft.padding.only(left=10),
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        bgcolor=card_color,
                    ),
                    elevation=1,
                )
            )

        # Кнопки быстрого выбора
        select_all_btn = ft.TextButton(
            translator.get("select_all"),
            icon=ft.icons.SELECT_ALL,
            on_click=lambda e: self._toggle_all_metadata(file_type, True),
        )

        deselect_all_btn = ft.TextButton(
            translator.get("deselect_all"),
            icon=ft.icons.DESELECT,
            on_click=lambda e: self._toggle_all_metadata(file_type, False),
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                translator.get(
                                    f"metadata_for_{file_type.replace(' ', '_')}"
                                ),
                                size=16,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Container(expand=True),
                            select_all_btn,
                            deselect_all_btn,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column(
                            switches,
                            spacing=8,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        height=400,  # Фиксированная высота для прокрутки
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.all(16),
        )

    def _on_metadata_switch_change(self, e, file_type: str, field_key: str):
        """Обработчик изменения переключателя метаданных"""
        self.current_settings["file_type_settings"][file_type][field_key] = e.control.value
        # Обновляем цвет карточки с учетом темы
        card = e.control.parent.parent.parent
        card_color, text_color = self._get_card_colors(e.control.value)
        card.bgcolor = card_color
        
        # Обновляем цвет текста описания
        description_text = e.control.parent.parent.controls[1].content
        if hasattr(description_text, 'color'):
            description_text.color = text_color if text_color != ft.colors.ON_SURFACE else ft.colors.ON_SURFACE_VARIANT
        
        self.page.update()

    def _toggle_all_metadata(self, file_type: str, select_all: bool):
        """Переключить все метаданные для типа файла"""
        # Обновляем настройки
        for field_key in self.current_settings["file_type_settings"][file_type]:
            self.current_settings["file_type_settings"][file_type][field_key] = select_all
        
        # Находим и обновляем только нужную вкладку
        self._update_metadata_tab(file_type)
        self.page.update()

    def _update_metadata_tab(self, file_type: str):
        """Обновляет содержимое конкретной вкладки метаданных"""
        try:
            tabs_container = self.dialog.content.content
            if hasattr(tabs_container, 'tabs'):
                # Запоминаем текущий выбранный индекс
                current_tab_index = getattr(tabs_container, 'selected_index', 0)
                
                for i, tab in enumerate(tabs_container.tabs):
                    current_file_type = self._get_current_tab_file_type(tab.text)
                    if current_file_type == file_type:
                        # Перестраиваем только содержимое этой вкладки
                        tab.content = self._build_metadata_tab(file_type)
                        
                        # Восстанавливаем выбранную вкладку
                        tabs_container.selected_index = current_tab_index
                        break
        except Exception as e:
            # В случае ошибки делаем полную перестройку с сохранением вкладки
            try:
                current_tab_index = getattr(self.dialog.content.content, 'selected_index', 0)
                self.dialog.content = self._build_content()
                self.dialog.content.content.selected_index = current_tab_index
            except:
                self.dialog.content = self._build_content()

    def _build_about_tab(self) -> ft.Container:
        """Вкладка о программе"""
        return ft.Container(
            content=ft.Column(
                [
                    # Логотип и название
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.icons.CLEANING_SERVICES_ROUNDED,
                                    size=64,
                                    color=ft.colors.PRIMARY,
                                ),
                                ft.Text(
                                    translator.get("app_title"),
                                    size=24,
                                    weight=ft.FontWeight.W_600,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    translator.get("app_version"),
                                    size=14,
                                    color=ft.colors.ON_SURFACE_VARIANT,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.all(20),
                    ),
                    # Описание
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        translator.get("about_program"),
                                        size=16,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        translator.get("app_description"),
                                        size=13,
                                        color=ft.colors.ON_SURFACE_VARIANT,
                                        text_align=ft.TextAlign.JUSTIFY,
                                    ),
                                ],
                                spacing=8,
                            ),
                            padding=ft.padding.all(16),
                        ),
                        elevation=1,
                    ),
                    # Поддерживаемые форматы
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        translator.get("supported_formats"),
                                        size=16,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Row(
                                        [
                                            ft.Column(
                                                [
                                                    ft.Row(
                                                        [
                                                            ft.Icon(
                                                                ft.icons.IMAGE,
                                                                size=16,
                                                                color=ft.colors.PRIMARY,
                                                            ),
                                                            ft.Text(
                                                                translator.get(
                                                                    "images"
                                                                ),
                                                                weight=ft.FontWeight.W_500,
                                                            ),
                                                        ],
                                                        spacing=8,
                                                    ),
                                                    ft.Container(
                                                        content=ft.Text(
                                                            translator.get(
                                                                "supported_images_formats"
                                                            ),
                                                            size=12,
                                                            color=ft.colors.ON_SURFACE_VARIANT,
                                                        ),
                                                        padding=ft.padding.only(
                                                            left=24
                                                        ),
                                                    ),
                                                ],
                                                spacing=4,
                                                expand=True,
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Row(
                                                        [
                                                            ft.Icon(
                                                                ft.icons.DESCRIPTION,
                                                                size=16,
                                                                color=ft.colors.PRIMARY,
                                                            ),
                                                            ft.Text(
                                                                translator.get(
                                                                    "documents"
                                                                ),
                                                                weight=ft.FontWeight.W_500,
                                                            ),
                                                        ],
                                                        spacing=8,
                                                    ),
                                                    ft.Container(
                                                        content=ft.Text(
                                                            translator.get(
                                                                "supported_docs_formats"
                                                            ),
                                                            size=12,
                                                            color=ft.colors.ON_SURFACE_VARIANT,
                                                        ),
                                                        padding=ft.padding.only(
                                                            left=24
                                                        ),
                                                    ),
                                                ],
                                                spacing=4,
                                                expand=True,
                                            ),
                                        ]
                                    ),
                                    ft.Container(height=8),
                                    ft.Row(
                                        [
                                            ft.Column(
                                                [
                                                    ft.Row(
                                                        [
                                                            ft.Icon(
                                                                ft.icons.PICTURE_AS_PDF,
                                                                size=16,
                                                                color=ft.colors.PRIMARY,
                                                            ),
                                                            ft.Text(
                                                                translator.get(
                                                                    "pdf", case="upper"
                                                                ),
                                                                weight=ft.FontWeight.W_500,
                                                            ),
                                                        ],
                                                        spacing=8,
                                                    ),
                                                    ft.Container(
                                                        content=ft.Text(
                                                            translator.get(
                                                                "supported_pdf_formats"
                                                            ),
                                                            size=12,
                                                            color=ft.colors.ON_SURFACE_VARIANT,
                                                        ),
                                                        padding=ft.padding.only(
                                                            left=24
                                                        ),
                                                    ),
                                                ],
                                                spacing=4,
                                                expand=True,
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Row(
                                                        [
                                                            ft.Icon(
                                                                ft.icons.VIDEOCAM,
                                                                size=16,
                                                                color=ft.colors.PRIMARY,
                                                            ),
                                                            ft.Text(
                                                                translator.get("video"),
                                                                weight=ft.FontWeight.W_500,
                                                            ),
                                                        ],
                                                        spacing=8,
                                                    ),
                                                    ft.Container(
                                                        content=ft.Text(
                                                            translator.get(
                                                                "supported_video_formats"
                                                            ),
                                                            size=12,
                                                            color=ft.colors.ON_SURFACE_VARIANT,
                                                        ),
                                                        padding=ft.padding.only(
                                                            left=24
                                                        ),
                                                    ),
                                                ],
                                                spacing=4,
                                                expand=True,
                                            ),
                                        ]
                                    ),
                                ],
                                spacing=12,
                            ),
                            padding=ft.padding.all(16),
                        ),
                        elevation=1,
                    ),
                    # Приватность и безопасность
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        translator.get("privacy_security"),
                                        size=16,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        translator.get("privacy_info"),
                                        size=13,
                                        color=ft.colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=8,
                            ),
                            padding=ft.padding.all(16),
                        ),
                        elevation=1,
                    ),
                    # Документы
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        translator.get("legal_info"),
                                        size=16,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Row(
                                        [
                                            ft.OutlinedButton(
                                                content=ft.Row(
                                                    [
                                                        ft.Icon(
                                                            ft.icons.PRIVACY_TIP,
                                                            size=16,
                                                        ),
                                                        ft.Text(
                                                            translator.get(
                                                                "read_privacy_policy"
                                                            ),
                                                            size=12,
                                                        ),
                                                    ],
                                                    spacing=6,
                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                ),
                                                on_click=self._show_privacy_policy,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(
                                                        radius=8
                                                    ),
                                                    padding=ft.padding.symmetric(
                                                        horizontal=12, vertical=8
                                                    ),
                                                ),
                                            ),
                                            ft.OutlinedButton(
                                                content=ft.Row(
                                                    [
                                                        ft.Icon(
                                                            ft.icons.GAVEL, size=16
                                                        ),
                                                        ft.Text(
                                                            translator.get(
                                                                "read_terms_of_service"
                                                            ),
                                                            size=12,
                                                        ),
                                                    ],
                                                    spacing=6,
                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                ),
                                                on_click=self._show_terms_of_service,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(
                                                        radius=8
                                                    ),
                                                    padding=ft.padding.symmetric(
                                                        horizontal=12, vertical=8
                                                    ),
                                                ),
                                            ),
                                        ],
                                        spacing=12,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        wrap=True,
                                    ),
                                ],
                                spacing=12,
                            ),
                            padding=ft.padding.all(16),
                        ),
                        elevation=1,
                    ),
                    # Разработчик и лицензия
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.GestureDetector(
                                    content=ft.Text(
                                        translator.get("copyright"),
                                        size=12,
                                        color=ft.colors.PRIMARY,
                                        text_align=ft.TextAlign.CENTER,
                                        style=ft.TextStyle(
                                            decoration=ft.TextDecoration.UNDERLINE
                                        ),
                                    ),
                                    on_tap=lambda e: self.page.launch_url(
                                        translator.get("github_link")
                                    ),
                                ),
                                ft.Text(
                                    translator.get("license_flet"),
                                    size=12,
                                    color=ft.colors.ON_SURFACE_VARIANT,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            spacing=4,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=16),
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

    def _get_file_type_name(self, file_type: str) -> str:
        """Получить читаемое название типа файла"""
        names = {
            "image": translator.get("images"),
            "document": translator.get("documents"),
            "pdf": translator.get("pdf"),
            "video": translator.get("video"),
        }
        return names.get(file_type, file_type)



    def _cancel(self, e):
        """Отмена изменений"""
        self.dialog.open = False
        self.page.update()

    def _reset_defaults(self, e):
        """Сброс к настройкам по умолчанию"""
        # Сохраняем текущий язык для проверки
        old_language = self.current_settings.get("language", "ru")
        
        # Восстанавливаем дефолтные настройки (как в __init__)
        self.current_settings = {
            "theme": "system",
            "output_mode": "create_copy",
            "create_backup": True,
            "language": "ru",
            "file_type_settings": {
                "image": {
                    # EXIF данные
                    "exif_author": True,        # Автор фотографии
                    "exif_copyright": True,     # Авторские права
                    "exif_datetime": True,      # Дата и время съемки
                    "exif_camera": True,        # Модель камеры и настройки
                    "exif_software": True,      # ПО для обработки
                    # GPS данные
                    "gps_coords": True,         # GPS координаты
                    "gps_altitude": True,       # Высота над уровнем моря
                    # Персональные данные
                    "camera_owner": True,       # Владелец камеры
                    "camera_serial": True,      # Серийный номер камеры
                    "user_comments": True,      # Комментарии пользователя
                },
                "document": {
                    # Авторские данные
                    "author": True,             # Автор документа
                    "last_modified_by": True,   # Последний редактор
                    "company": True,            # Компания
                    # Временные данные
                    "created": True,            # Дата создания
                    "modified": True,           # Дата изменения
                    "last_printed": True,       # Дата последней печати
                    # Документооборот
                    "revision": True,           # Номер ревизии
                    "version": True,            # Версия документа
                    "content_status": True,     # Статус контента
                    "category": True,           # Категория
                    "language": True,           # Язык документа
                    "identifier": True,         # Уникальный идентификатор
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Заголовок
                    "subject": False,           # Тема
                    "keywords": False,          # Ключевые слова
                    "comments": False,          # Комментарии к содержанию
                },
                "pdf": {
                    # Авторские данные
                    "author": True,             # Автор PDF
                    "creator": True,            # Создатель (программа)
                    "producer": True,           # Производитель PDF
                    # Временные данные
                    "created": True,            # Дата создания
                    "modified": True,           # Дата изменения
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Заголовок документа
                    "subject": False,           # Тема документа
                    "keywords": False,          # Ключевые слова
                },
                "video": {
                    # Авторские данные
                    "author": True,             # Автор/создатель видео
                    "encoder": True,            # Энкодер/программа записи
                    # Временные данные
                    "creation_time": True,      # Дата и время создания
                    # GPS и локация
                    "gps_coords": True,         # GPS координаты
                    "location": True,           # Информация о местоположении
                    # Техническая информация
                    "major_brand": True,        # Основной бренд контейнера
                    "compatible_brands": True,  # Совместимые форматы
                    # Контент (по умолчанию НЕ удаляем)
                    "title": False,             # Название видео
                    "comment": False,           # Комментарии/описание
                    "description": False,       # Подробное описание
                },
            },
        }

        # Вызываем callback для сохранения новых настроек ПЕРЕД изменением переводчика
        # Это важно чтобы основное приложение правильно определило изменение языка
        if self.on_save:
            self.on_save(self.current_settings)
        
        # Если язык изменился, перестраиваем диалог с новыми переводами
        if old_language != "ru":
            # Полностью перестраиваем диалог с новыми переводами
            self.dialog.content = self._build_content()
            
            # Обновляем заголовок диалога
            self.dialog.title = ft.Row(
                [
                    ft.Icon(ft.icons.SETTINGS, size=24),
                    ft.Text(
                        translator.get("settings"), size=20, weight=ft.FontWeight.W_600
                    ),
                ],
                spacing=8,
            )
            
            # Обновляем кнопки диалога
            self.dialog.actions = [
                ft.TextButton(
                    translator.get("cancel"),
                    on_click=self._cancel,
                    style=ft.ButtonStyle(
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                ),
                ft.TextButton(
                    translator.get("reset_defaults"),
                    on_click=self._reset_defaults,
                    style=ft.ButtonStyle(
                        color=ft.colors.PRIMARY,
                    ),
                ),
                ft.FilledButton(
                    translator.get("save"),
                    icon=ft.icons.SAVE,
                    on_click=self._save_settings,
                ),
            ]
        else:
            # Если язык не изменился, просто обновляем UI
            self.dialog.content = self._build_content()
        
        self.page.update()

    def _save_settings(self, e):
        """Сохранение настроек"""
        # Собираем текущие значения из UI
        settings = {
            "theme": self.theme_dropdown.value,
            "output_mode": self.output_mode_dropdown.value,
            "language": self.language_dropdown.value,
            "file_type_settings": self.current_settings["file_type_settings"].copy(),
        }

        # Обновляем настройки метаданных из переключателей
        tabs_content = self.dialog.content.content
        for tab in tabs_content.tabs:
            if hasattr(tab.content, "content") and hasattr(
                tab.content.content, "controls"
            ):
                for control in tab.content.content.controls:
                    if isinstance(control, ft.Column):
                        for item in control.controls:
                            if isinstance(item, ft.Card) and hasattr(
                                item.content, "content"
                            ):
                                if hasattr(item.content.content, "controls"):
                                    for subitem in item.content.content.controls:
                                        if isinstance(subitem, ft.Row):
                                            for element in subitem.controls:
                                                if isinstance(
                                                    element, ft.Switch
                                                ) and hasattr(element, "data"):
                                                    file_type = (
                                                        self._get_current_tab_file_type(
                                                            tab.text
                                                        )
                                                    )
                                                    if (
                                                        file_type
                                                        and file_type
                                                        in settings[
                                                            "file_type_settings"
                                                        ]
                                                    ):
                                                        settings["file_type_settings"][
                                                            file_type
                                                        ][element.data] = element.value

        # Вызываем callback для сохранения
        if self.on_save:
            self.on_save(settings)

        # Если язык изменился, перестраиваем интерфейс
        if settings["language"] != self.current_settings["language"]:
            self.current_settings = settings
            # Устанавливаем новый язык для переводчика
            translator.set_language(settings["language"])
            # Перестраиваем контент с новыми переводами
            self.dialog.content = self._build_content()
            # Обновляем заголовок и кнопки
            self.dialog.title = ft.Row(
                [
                    ft.Icon(ft.icons.SETTINGS, size=24),
                    ft.Text(
                        translator.get("settings"), size=20, weight=ft.FontWeight.W_600
                    ),
                ],
                spacing=8,
            )
            self.dialog.actions = [
                ft.TextButton(
                    translator.get("cancel"),
                    on_click=self._cancel,
                    style=ft.ButtonStyle(
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                ),
                ft.TextButton(
                    translator.get("reset_defaults"),
                    on_click=self._reset_defaults,
                    style=ft.ButtonStyle(
                        color=ft.colors.PRIMARY,
                    ),
                ),
                ft.FilledButton(
                    translator.get("save"),
                    icon=ft.icons.SAVE,
                    on_click=self._save_settings,
                ),
            ]
        else:
            # Если язык не изменился, обновляем текущие настройки но оставляем диалог открытым
            self.current_settings = settings
        
        self.page.update()

    def _get_current_tab_file_type(self, tab_text: str) -> str | None:
        """Получить тип файла по названию вкладки"""
        mapping = {
            translator.get("images"): "image",
            translator.get("documents"): "document",
            translator.get("pdf"): "pdf",
            translator.get("video"): "video",
        }
        return mapping.get(tab_text)

    def _get_privacy_policy_text(self, lang: str) -> str:
        """Получить текст политики конфиденциальности"""
        if lang == "ru":
            return """ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ

Metadata Cleaner

Дата вступления в силу: 23 июня 2025 г.

ПРИНЦИПЫ КОНФИДЕНЦИАЛЬНОСТИ

Локальная обработка данных:
• Все файлы обрабатываются исключительно на вашем устройстве
• Приложение не передает ваши файлы или данные через интернет
• Никакая информация не отправляется на внешние серверы

Прозрачность:
• Исходный код приложения открыт для проверки
• Все операции с файлами выполняются с вашего согласия
• Вы контролируете весь процесс обработки данных

СОБИРАЕМАЯ ИНФОРМАЦИЯ

Информация, которую мы НЕ собираем:
• Личные данные: имена, адреса, номера телефонов или email
• Содержимое файлов: не анализируем и не сохраняем содержимое ваших файлов
• Метаданные: удаленные метаданные не сохраняются и не передаются
• Данные об использовании: не отслеживаем, какие файлы вы обрабатываете
• Аналитика: приложение не содержит систем аналитики или трекинга

Локальные настройки:
• Настройки приложения: сохраняются локально (тема, язык, режимы работы)
• Пути к файлам: временно используются только для обработки
• Логи ошибок: создаются локально для диагностики проблем

БЕЗОПАСНОСТЬ ДАННЫХ

Технические меры:
• Локальное выполнение: все операции выполняются на вашем устройстве
• Отсутствие сетевого доступа: приложение не требует подключения к интернету
• Изолированная обработка: каждый файл обрабатывается независимо
• Временные файлы: автоматически удаляются после обработки

ПРАВА ПОЛЬЗОВАТЕЛЕЙ

Ваши права:
• Полный контроль: вы контролируете все операции с вашими файлами
• Отзыв согласия: можете остановить обработку в любой момент
• Доступ к коду: исходный код доступен для проверки
• Удаление данных: можете удалить приложение и все связанные файлы

КОНТАКТНАЯ ИНФОРМАЦИЯ

Для вопросов о конфиденциальности:
GitHub: https://github.com/AntGalanin06/Metadata_Cleaner

ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ

Приложение "Metadata Cleaner" разработано с учетом максимальной защиты вашей приватности. Мы не собираем, не храним и не передаем ваши личные данные или файлы.

Последнее обновление: 25 июня 2025 г."""
        else:
            return """PRIVACY POLICY

Metadata Cleaner

Effective Date: June 23, 2025

PRIVACY PRINCIPLES

Local Data Processing:
• All files are processed exclusively on your device
• The application does not transmit your files or data over the internet
• No information is sent to external servers

Transparency:
• The application's source code is open for inspection
• All file operations are performed with your consent
• You control the entire data processing workflow

INFORMATION COLLECTION

Information we DO NOT collect:
• Personal Data: We do not collect names, addresses, phone numbers, or emails
• File Content: We do not analyze or store the content of your files
• Metadata: Removed metadata is not saved or transmitted
• Usage Data: We do not track which files you process
• Analytics: The application contains no analytics or tracking systems

Local Settings:
• Application Settings: Saved locally (theme, language, operation modes)
• File Paths: Used temporarily only for processing
• Error Logs: Created locally for troubleshooting

DATA SECURITY

Technical Measures:
• Local Execution: All operations are performed on your device
• No Network Access: The application does not require internet connection
• Isolated Processing: Each file is processed independently
• Temporary Files: Automatically deleted after processing

USER RIGHTS

Your Rights:
• Full Control: You control all operations with your files
• Consent Withdrawal: You can stop processing at any time
• Code Access: Source code is available for inspection
• Data Deletion: You can delete the application and all related files

CONTACT INFORMATION

For privacy-related questions:
GitHub: https://github.com/AntGalanin06/Metadata_Cleaner

FINAL PROVISIONS

The "Metadata Cleaner" application is designed with maximum privacy protection in mind. We do not collect, store, or transmit your personal data or files.

Last Updated: June 25, 2025"""

    def _get_terms_of_service_text(self, lang: str) -> str:
        """Получить текст пользовательского соглашения"""
        if lang == "ru":
            return """ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ

Metadata Cleaner

Дата вступления в силу: 23 июня 2025 г.

Загружая, устанавливая или используя приложение "Metadata Cleaner", вы соглашаетесь с условиями настоящего Пользовательского соглашения.

1. ОПИСАНИЕ ПРИЛОЖЕНИЯ

Приложение предназначено для удаления метаданных из различных типов файлов:
• Изображения (JPG, JPEG, PNG, GIF, HEIC, HEIF)
• Документы (DOCX, PPTX, XLSX)
• PDF файлы
• Видеофайлы (MP4, MOV)

Функциональность:
• Локальная обработка файлов на устройстве пользователя
• Создание резервных копий (опционально)
• Пакетная обработка файлов
• Графический интерфейс с поддержкой тем

2. ЛИЦЕНЗИЯ И ПРАВА ИСПОЛЬЗОВАНИЯ

Приложение распространяется под лицензией MIT, которая предоставляет право:
• Использовать в личных и коммерческих целях
• Изучать исходный код
• Модифицировать код для собственных нужд
• Распространять оригинальную или модифицированную версию

3. ОБЯЗАННОСТИ ПОЛЬЗОВАТЕЛЯ

Вы обязуетесь:
• Использовать приложение только для законных целей
• Обрабатывать только файлы, на которые у вас есть права
• Соблюдать авторские права третьих лиц
• Создавать резервные копии важных файлов перед обработкой

4. ОГРАНИЧЕНИЕ ОТВЕТСТВЕННОСТИ

Приложение предоставляется "как есть" без гарантий:
• Мы не гарантируем безошибочную работу
• Не несем ответственности за потерю данных
• Не гарантируем совместимость с вашей системой

5. КОНФИДЕНЦИАЛЬНОСТЬ

• Приложение не собирает личные данные пользователей
• Все файлы обрабатываются локально на вашем устройстве
• Никакая информация не передается через интернет

6. ТЕХНИЧЕСКАЯ ПОДДЕРЖКА

Поддержка предоставляется через:
• GitHub Issues в репозитории проекта
• Документацию в репозитории

7. КОНТАКТНАЯ ИНФОРМАЦИЯ

GitHub: https://github.com/AntGalanin06/Metadata_Cleaner

Используя приложение "Metadata Cleaner", вы подтверждаете, что прочитали, поняли и согласились с условиями настоящего Пользовательского соглашения.

Последнее обновление: 25 июня 2025 г."""
        else:
            return """TERMS OF SERVICE

Metadata Cleaner

Effective Date: June 23, 2025

By downloading, installing, or using the "Metadata Cleaner" application, you agree to the terms of this Terms of Service.

1. APPLICATION DESCRIPTION

The Application is designed to remove metadata from various file types:
• Images (JPG, JPEG, PNG, GIF, HEIC, HEIF)
• Documents (DOCX, PPTX, XLSX)
• PDF files
• Video files (MP4, MOV)

Functionality:
• Local file processing on the user's device
• Backup creation (optional)
• Batch file processing
• Graphical interface with theme support

2. LICENSE AND USAGE RIGHTS

The Application is distributed under the MIT license, which grants you the right to:
• Use for personal and commercial purposes
• Study the source code
• Modify the code for your own needs
• Distribute the original or modified version

3. USER OBLIGATIONS

You agree to:
• Use the Application only for lawful purposes
• Process only files to which you have rights
• Respect third-party copyrights
• Create backups of important files before processing

4. LIMITATION OF LIABILITY

The Application is provided "as is" without any warranties:
• We do not guarantee error-free operation
• We are not responsible for data loss
• We do not guarantee compatibility with your system

5. PRIVACY

• The Application does not collect users' personal data
• All files are processed locally on your device
• No information is transmitted over the internet

6. TECHNICAL SUPPORT

Support is provided through:
• GitHub Issues in the project repository
• Documentation in the repository

7. CONTACT INFORMATION

GitHub: https://github.com/AntGalanin06/Metadata_Cleaner

By using the "Metadata Cleaner" Application, you confirm that you have read, understood, and agreed to the terms of this Terms of Service.

Last Updated: June 25, 2025"""

    def _parse_text_with_links(self, content: str) -> ft.Column:
        """Парсит текст и создает компоненты с кликабельными ссылками"""
        lines = content.split('\n')
        controls = []
        
        for line in lines:
            if 'https://github.com/AntGalanin06/Metadata_Cleaner' in line:
                # Разбиваем строку на части до и после ссылки
                parts = line.split('https://github.com/AntGalanin06/Metadata_Cleaner')
                row_controls = []
                
                if parts[0]:
                    row_controls.append(
                        ft.Text(
                            parts[0],
                            size=14,
                            color=ft.colors.ON_SURFACE,
                        )
                    )
                
                # Создаем кликабельную ссылку
                row_controls.append(
                    ft.GestureDetector(
                        content=ft.Text(
                            "https://github.com/AntGalanin06/Metadata_Cleaner",
                            size=14,
                            color=ft.colors.PRIMARY,
                            style=ft.TextStyle(
                                decoration=ft.TextDecoration.UNDERLINE
                            ),
                        ),
                        on_tap=lambda e: self.page.launch_url(
                            "https://github.com/AntGalanin06/Metadata_Cleaner"
                        ),
                    )
                )
                
                if len(parts) > 1 and parts[1]:
                    row_controls.append(
                        ft.Text(
                            parts[1],
                            size=14,
                            color=ft.colors.ON_SURFACE,
                        )
                    )
                
                controls.append(
                    ft.Row(
                        controls=row_controls,
                        wrap=True,
                    )
                )
            else:
                controls.append(
                    ft.Text(
                        line,
                        size=14,
                        selectable=True,
                        color=ft.colors.ON_SURFACE,
                    )
                )
        
        return ft.Column(
            controls=controls,
            spacing=2,
            scroll=ft.ScrollMode.ADAPTIVE,
        )

    def _show_document_dialog(self, title: str, content: str):
        """Показать диалог с документом"""
        # Создаем контент с кликабельными ссылками
        parsed_content = self._parse_text_with_links(content)
        
        doc_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.icons.ARTICLE, size=24, color=ft.colors.PRIMARY),
                    ft.Text(title, size=20, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Container(
                    content=parsed_content,
                    width=700,
                    height=500,
                    padding=ft.padding.all(24),
                    border_radius=12,
                    bgcolor=ft.colors.SURFACE,
                ),
                width=750,
                height=550,
            ),
            actions=[
                ft.FilledButton(
                    translator.get("close"),
                    icon=ft.icons.CLOSE,
                    on_click=lambda e: self._close_document_dialog(doc_dialog),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = doc_dialog
        doc_dialog.open = True
        self.page.update()

    def _close_document_dialog(self, dialog):
        """Закрыть диалог документа и показать настройки"""
        dialog.open = False
        self.page.dialog = None
        # Показываем диалог настроек заново
        self.show()
        self.page.update()

    def _show_privacy_policy(self, e):
        """Показать политику конфиденциальности"""
        lang = self.current_settings.get("language", "ru")
        content = self._get_privacy_policy_text(lang)
        title = translator.get("privacy_policy")
        self._show_document_dialog(title, content)

    def _show_terms_of_service(self, e):
        """Показать пользовательское соглашение"""
        lang = self.current_settings.get("language", "ru")
        content = self._get_terms_of_service_text(lang)
        title = translator.get("terms_of_service")
        self._show_document_dialog(title, content)
