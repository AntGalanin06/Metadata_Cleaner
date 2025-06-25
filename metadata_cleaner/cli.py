#!/usr/bin/env python3

"""Командная строка для Metadata Cleaner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cleaner import MetadataDispatcher
from .cleaner.models import CleaningOptions


def parse_args():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Очистка метаданных из файлов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s file1.pdf file2.docx file3.jpg
  %(prog)s *.pdf --no-backup
  %(prog)s document.docx --keep-title --keep-subject
        """,
    )

    parser.add_argument("files", nargs="+", help="Файлы для обработки")

    # Опции очистки
    parser.add_argument(
        "--keep-author", action="store_true", help="Сохранить автора/создателя"
    )

    parser.add_argument(
        "--keep-dates", action="store_true", help="Сохранить даты создания/изменения"
    )

    parser.add_argument(
        "--keep-comments", action="store_true", help="Сохранить комментарии"
    )

    parser.add_argument("--keep-gps", action="store_true", help="Сохранить GPS данные")

    parser.add_argument(
        "--keep-camera", action="store_true", help="Сохранить данные камеры"
    )

    parser.add_argument("--keep-title", action="store_true", help="Сохранить заголовок")

    parser.add_argument("--keep-subject", action="store_true", help="Сохранить тему")

    parser.add_argument(
        "--keep-keywords", action="store_true", help="Сохранить ключевые слова"
    )

    # Общие опции
    parser.add_argument(
        "--no-backup", action="store_true", help="Не создавать резервные копии"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")

    parser.add_argument("--quiet", "-q", action="store_true", help="Тихий режим")

    return parser.parse_args()


def create_options(args) -> CleaningOptions:
    """Создание опций очистки из аргументов."""
    return CleaningOptions(
        clean_author=not args.keep_author,
        clean_created_date=not args.keep_dates,
        clean_modified_date=not args.keep_dates,
        clean_comments=not args.keep_comments,
        clean_gps_data=not args.keep_gps,
        clean_camera_info=not args.keep_camera,
        clean_title=not args.keep_title,
        clean_subject=not args.keep_subject,
        clean_keywords=not args.keep_keywords,
        create_backup=not args.no_backup,
    )


def process_files(
    files: list[str],
    options: CleaningOptions,
    verbose: bool = False,
    quiet: bool = False,
):
    """Обработка списка файлов."""
    from .services.settings_service import SettingsService
    
    settings_service = SettingsService()
    dispatcher = MetadataDispatcher(settings_service)

    total_files = len(files)
    processed = 0
    skipped = 0
    errors = 0

    if not quiet:
        print(f"Обработка {total_files} файлов...")

    for file_path in files:
        path = Path(file_path)

        if not path.exists():
            if not quiet:
                print(f"Ошибка: Файл не найден: {file_path}")
            errors += 1
            continue

        if not dispatcher.is_supported(file_path):
            if verbose and not quiet:
                print(f"Пропущен неподдерживаемый файл: {file_path}")
            skipped += 1
            continue

        try:
            if verbose and not quiet:
                print(f"Обработка: {file_path}")

            result = dispatcher.process_file_with_options(file_path, options)

            if result.status.value == "success":
                if not quiet:
                    print(f"✓ Обработан: {file_path}")
                processed += 1
            else:
                if not quiet:
                    print(f"✗ Ошибка в файле {file_path}: {result.message}")
                errors += 1

        except Exception as e:
            if not quiet:
                print(f"✗ Исключение при обработке {file_path}: {e}")
            errors += 1

    if not quiet:
        print(f"\nРезультат: {processed} обработано, {skipped} пропущено, {errors} ошибок")


def main():
    """Главная функция CLI."""
    try:
        args = parse_args()
        options = create_options(args)

        process_files(args.files, options, args.verbose, args.quiet)

    except KeyboardInterrupt:
        print("\nОперация прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
