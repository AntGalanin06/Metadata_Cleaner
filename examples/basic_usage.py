#!/usr/bin/env python3
"""Пример базового использования Metadata Cleaner."""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from metadata_cleaner.cleaner import MetadataDispatcher
from metadata_cleaner.cleaner.models import CleaningOptions


def main():
    """Демонстрация базового использования."""

    # Создаем диспетчер
    dispatcher = MetadataDispatcher()

    # Настройки очистки
    options = CleaningOptions(
        clean_author=True,
        clean_created_date=True,
        clean_modified_date=True,
        clean_comments=True,
        clean_gps_data=True,
        clean_camera_info=True,
        clean_title=False,
        clean_subject=False,
        clean_keywords=False,
    )

    # Пример файлов для обработки
    test_files = ["example.docx", "example.pdf", "example.jpg", "example.mp4"]

    # Показываем поддерживаемые расширения
    for _ext in sorted(dispatcher.SUPPORTED_EXTENSIONS):
        pass

    # Проверяем каждый файл
    for file_path in test_files:
        # Проверяем поддержку
        if dispatcher.is_supported(file_path):
            # Получаем информацию о файле
            dispatcher.get_file_info(file_path)

            # Если файл существует, можно попробовать очистить
            if Path(file_path).exists():
                try:
                    result = dispatcher.process_file_with_options(file_path, options)
                    if result.message:
                        pass
                except Exception:
                    pass
            else:
                pass
        else:
            pass


if __name__ == "__main__":
    main()
