#!/usr/bin/env python3
"""Скрипт для запуска тестов с различными опциями."""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description="", check=True):
    """Запускает команду и выводит результат."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Команда: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, check=check, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - УСПЕШНО")
        else:
            print(f"❌ {description} - ОШИБКА (код: {result.returncode})")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ОШИБКА: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Команда не найдена: {cmd[0]}")
        return False


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description="Скрипт для запуска тестов Metadata Cleaner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python scripts/run_tests.py --all              # Все тесты
  python scripts/run_tests.py --unit             # Только unit тесты
  python scripts/run_tests.py --integration      # Только интеграционные тесты
  python scripts/run_tests.py --performance      # Тесты производительности
  python scripts/run_tests.py --coverage         # С отчетом покрытия
  python scripts/run_tests.py --quick            # Быстрые тесты
  python scripts/run_tests.py --html             # HTML отчет покрытия
  python scripts/run_tests.py --ci               # Режим для CI/CD
        """,
    )

    # Группы тестов
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--all", action="store_true", help="Запустить все тесты")
    test_group.add_argument("--unit", action="store_true", help="Только unit тесты")
    test_group.add_argument(
        "--integration", action="store_true", help="Только интеграционные тесты"
    )
    test_group.add_argument(
        "--performance", action="store_true", help="Тесты производительности"
    )
    test_group.add_argument(
        "--quick", action="store_true", help="Быстрые тесты (без медленных)"
    )

    # Опции отчетности
    parser.add_argument(
        "--coverage", action="store_true", help="Генерировать отчет покрытия"
    )
    parser.add_argument("--html", action="store_true", help="HTML отчет покрытия")
    parser.add_argument("--xml", action="store_true", help="XML отчет покрытия")
    parser.add_argument("--json", action="store_true", help="JSON отчет покрытия")

    # Режимы запуска
    parser.add_argument("--ci", action="store_true", help="Режим для CI/CD")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--quiet", "-q", action="store_true", help="Тихий режим")
    parser.add_argument(
        "--parallel", "-n", type=int, help="Количество параллельных процессов"
    )

    # Дополнительные опции
    parser.add_argument("--no-cov", action="store_true", help="Отключить покрытие кода")
    parser.add_argument("--files", nargs="+", help="Конкретные файлы для тестирования")
    parser.add_argument("--pattern", "-k", help="Паттерн для фильтрации тестов")

    args = parser.parse_args()

    # Определяем корневую директорию проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    # Базовая команда pytest
    cmd = [sys.executable, "-m", "pytest"]

    # Добавляем опции вербальности
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    else:
        cmd.append("--tb=short")  # Краткий traceback по умолчанию

    # Параллельное выполнение
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Покрытие кода
    if not args.no_cov and (
        args.coverage or args.html or args.xml or args.json or args.ci
    ):
        cmd.extend(["--cov=metadata_cleaner", "--cov-report=term-missing"])

        if args.html or args.ci:
            cmd.append("--cov-report=html")

        if args.xml or args.ci:
            cmd.append("--cov-report=xml")

        if args.json:
            cmd.append("--cov-report=json")

    # Выбор тестов
    if args.unit:
        cmd.extend(["-m", "unit"])
        description = "Unit тесты"
    elif args.integration:
        cmd.extend(["-m", "integration"])
        description = "Интеграционные тесты"
    elif args.performance:
        cmd.extend(["-m", "slow"])
        description = "Тесты производительности"
    elif args.quick:
        cmd.extend(["-m", "not slow"])
        description = "Быстрые тесты"
    else:
        description = "Все тесты"

    # Конкретные файлы
    if args.files:
        cmd.extend(args.files)
        description = f"Тесты из файлов: {', '.join(args.files)}"
    else:
        cmd.append("tests/")

    # Паттерн фильтрации
    if args.pattern:
        cmd.extend(["-k", args.pattern])
        description += f" (паттерн: {args.pattern})"

    # CI режим
    if args.ci:
        cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])
        description = "CI/CD тесты"

    print("🧪 Metadata Cleaner Test Runner")
    print("=" * 60)
    print(f"📁 Рабочая директория: {project_root}")
    print(f"🎯 Режим: {description}")

    # Проверяем наличие тестовых файлов
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        print("❌ Директория tests/ не найдена!")
        return 1

    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        print("❌ Тестовые файлы не найдены!")
        return 1

    print(f"📋 Найдено тестовых файлов: {len(test_files)}")

    # Запускаем тесты
    success = run_command(cmd, description)

    # Дополнительные отчеты
    if success and (args.html or args.ci):
        html_dir = project_root / "htmlcov"
        if html_dir.exists():
            index_file = html_dir / "index.html"
            if index_file.exists():
                print(f"\n📊 HTML отчет покрытия: file://{index_file.absolute()}")

    if success and (args.xml or args.ci):
        xml_file = project_root / "coverage.xml"
        if xml_file.exists():
            print(f"📄 XML отчет покрытия: {xml_file}")

    # Итоговый результат
    print(f"\n{'='*60}")
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✨ Отличная работа!")
    else:
        print("💥 НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("🔧 Проверьте ошибки выше и исправьте их")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
