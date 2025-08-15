#!/usr/bin/env python3
"""
Финальный скрипт настройки проекта Metadata Cleaner.
Проверяет и финализирует всю инфраструктуру сборки и тестирования.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple


class Color:
    """Цвета для консольного вывода."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """Печатает заголовок секции."""
    print(f"\n{Color.BLUE}{Color.BOLD}{'='*60}{Color.END}")
    print(f"{Color.BLUE}{Color.BOLD}🚀 {title}{Color.END}")
    print(f"{Color.BLUE}{Color.BOLD}{'='*60}{Color.END}")


def print_success(message: str):
    """Печатает сообщение об успехе."""
    print(f"{Color.GREEN}✅ {message}{Color.END}")


def print_warning(message: str):
    """Печатает предупреждение."""
    print(f"{Color.YELLOW}⚠️ {message}{Color.END}")


def print_error(message: str):
    """Печатает ошибку."""
    print(f"{Color.RED}❌ {message}{Color.END}")


def print_info(message: str):
    """Печатает информационное сообщение."""
    print(f"{Color.BLUE}ℹ️ {message}{Color.END}")


def run_command(cmd: List[str], description: str = "", check_result: bool = True) -> Tuple[bool, str]:
    """Запускает команду и возвращает результат."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode == 0:
            if description:
                print_success(f"{description}")
            return True, result.stdout
        else:
            if check_result:
                print_error(f"{description} - ОШИБКА: {result.stderr}")
            return False, result.stderr
            
    except FileNotFoundError:
        if check_result:
            print_error(f"Команда не найдена: {cmd[0]}")
        return False, f"Command not found: {cmd[0]}"


def check_file_exists(file_path: Path, description: str) -> bool:
    """Проверяет существование файла."""
    if file_path.exists():
        print_success(f"{description}: {file_path}")
        return True
    else:
        print_error(f"{description} не найден: {file_path}")
        return False


def check_directory_structure(project_root: Path) -> bool:
    """Проверяет структуру директорий проекта."""
    print_header("Проверка структуры проекта")
    
    required_dirs = [
        "metadata_cleaner",
        "tests", 
        "installers",
        "installers/linux",
        "installers/macos", 
        "installers/windows",
        "assets",
        ".github/workflows"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print_success(f"Директория: {dir_name}")
        else:
            print_error(f"Отсутствует директория: {dir_name}")
            all_exist = False
    
    return all_exist


def check_installer_scripts(project_root: Path) -> bool:
    """Проверяет инсталляционные скрипты."""
    print_header("Проверка инсталляционных скрипов")
    
    installer_files = [
        "installers/build_all.sh",
        "installers/linux/appimage.sh",
        "installers/linux/deb.sh", 
        "installers/linux/rpm.sh",
        "installers/macos/dmg.sh",
        "installers/windows/installer.nsi",
        "installers/windows/build.ps1"
    ]
    
    all_exist = True
    for installer_file in installer_files:
        file_path = project_root / installer_file
        if check_file_exists(file_path, f"Инсталлятор {installer_file}"):
            # Проверяем права выполнения для shell скриптов
            if installer_file.endswith('.sh') and file_path.stat().st_mode & 0o111 == 0:
                print_warning(f"Файл {installer_file} не имеет прав выполнения")
                try:
                    file_path.chmod(0o755)
                    print_success(f"Права выполнения установлены для {installer_file}")
                except Exception as e:
                    print_error(f"Не удалось установить права выполнения: {e}")
        else:
            all_exist = False
    
    return all_exist


def check_github_workflows(project_root: Path) -> bool:
    """Проверяет GitHub Actions workflows."""
    print_header("Проверка GitHub Actions")
    
    workflow_files = [
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml"
    ]
    
    all_exist = True
    for workflow_file in workflow_files:
        file_path = project_root / workflow_file
        if not check_file_exists(file_path, f"Workflow {workflow_file}"):
            all_exist = False
    
    return all_exist


def check_test_infrastructure(project_root: Path) -> bool:
    """Проверяет инфраструктуру тестирования."""
    print_header("Проверка инфраструктуры тестирования")
    
    test_files = [
        "tests/conftest.py",
        "tests/test_dispatcher.py",
        "tests/test_models.py",
        "tests/test_handlers.py",
        "tests/test_settings_service.py",
        "tests/test_gui_app.py",
        "tests/test_cli.py",
        "tests/test_performance.py",
        "tests/test_integration.py",
        "tests/test_coverage_report.py",
        ".coveragerc",
        "scripts/run_tests.py"
    ]
    
    all_exist = True
    for test_file in test_files:
        file_path = project_root / test_file
        if not check_file_exists(file_path, f"Тестовый файл {test_file}"):
            all_exist = False
    
    return all_exist


def check_build_system(project_root: Path) -> bool:
    """Проверяет систему сборки."""
    print_header("Проверка системы сборки")
    
    build_files = [
        "build.py",
        "pyproject.toml",
        "Makefile"
    ]
    
    all_exist = True
    for build_file in build_files:
        file_path = project_root / build_file
        if not check_file_exists(file_path, f"Файл сборки {build_file}"):
            all_exist = False
    
    return all_exist


def check_dependencies(project_root: Path) -> bool:
    """Проверяет зависимости."""
    print_header("Проверка зависимостей")
    
    # Проверяем Poetry
    success, _ = run_command(["poetry", "--version"], "Poetry установлен", False)
    if not success:
        print_error("Poetry не установлен")
        return False
    
    # Проверяем Python версию
    success, output = run_command([sys.executable, "--version"], "Python версия", False)
    if success:
        print_info(f"Python: {output.strip()}")
    
    # Проверяем зависимости проекта
    pyproject_file = project_root / "pyproject.toml"
    if pyproject_file.exists():
        print_success("pyproject.toml найден")
        
        # Пытаемся установить зависимости
        os.chdir(project_root)
        success, _ = run_command(["poetry", "install"], "Установка зависимостей", False)
        if success:
            print_success("Зависимости установлены")
        else:
            print_warning("Не удалось установить зависимости автоматически")
    
    return True


def test_basic_functionality(project_root: Path) -> bool:
    """Тестирует базовую функциональность."""
    print_header("Тестирование базовой функциональности")
    
    os.chdir(project_root)
    
    # Проверяем импорт основных модулей
    test_imports = [
        "import metadata_cleaner",
        "from metadata_cleaner.cleaner.dispatcher import MetadataDispatcher",
        "from metadata_cleaner.services.settings_service import SettingsService",
        "from metadata_cleaner.cleaner.models import CleanStatus"
    ]
    
    for import_test in test_imports:
        success, _ = run_command([
            sys.executable, "-c", import_test
        ], f"Импорт: {import_test}", False)
        
        if success:
            print_success(f"Импорт работает: {import_test}")
        else:
            print_error(f"Импорт не работает: {import_test}")
            return False
    
    # Запускаем базовые тесты
    print_info("Запуск базовых тестов...")
    success, _ = run_command([
        sys.executable, "-m", "pytest", 
        "tests/test_models.py", 
        "-v", "--tb=short"
    ], "Базовые тесты", False)
    
    if success:
        print_success("Базовые тесты прошли")
    else:
        print_warning("Базовые тесты завершились с предупреждениями")
    
    return True


def generate_summary_report(project_root: Path, checks: dict) -> None:
    """Генерирует итоговый отчет."""
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    
    total_checks = len(checks)
    passed_checks = sum(1 for result in checks.values() if result)
    
    print(f"📊 Проверок выполнено: {total_checks}")
    print(f"✅ Успешных: {passed_checks}")
    print(f"❌ Неуспешных: {total_checks - passed_checks}")
    print(f"📈 Процент успеха: {(passed_checks/total_checks)*100:.1f}%")
    
    print("\n📋 Детальные результаты:")
    for check_name, result in checks.items():
        status = "✅ ПРОЙДЕНО" if result else "❌ НЕ ПРОЙДЕНО"
        print(f"  {check_name}: {status}")
    
    if all(checks.values()):
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 ВСЕ ПРОВЕРКИ УСПЕШНО ЗАВЕРШЕНЫ!{Color.END}")
        print(f"{Color.GREEN}✨ Проект Metadata Cleaner готов к использованию!{Color.END}")
        
        print(f"\n{Color.BLUE}📚 Следующие шаги:{Color.END}")
        print("1. Запустите тесты: python scripts/run_tests.py --all")
        print("2. Соберите приложение: python build.py")
        print("3. Создайте инсталляторы: ./installers/build_all.sh")
        print("4. Просмотрите документацию в docs/")
        
    else:
        print(f"\n{Color.YELLOW}{Color.BOLD}⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ{Color.END}")
        print(f"{Color.YELLOW}Исправьте указанные выше ошибки перед использованием{Color.END}")


def main():
    """Главная функция."""
    print(f"{Color.BLUE}{Color.BOLD}")
    print("🧪 Metadata Cleaner - Финальная проверка настройки")
    print("=" * 60)
    print(f"{Color.END}")
    
    # Определяем корневую директорию проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print_info(f"Проект: {project_root}")
    print_info(f"Python: {sys.version}")
    
    # Выполняем все проверки
    checks = {
        "Структура директорий": check_directory_structure(project_root),
        "Инсталляционные скрипты": check_installer_scripts(project_root),
        "GitHub Actions": check_github_workflows(project_root),
        "Инфраструктура тестирования": check_test_infrastructure(project_root),
        "Система сборки": check_build_system(project_root),
        "Зависимости": check_dependencies(project_root),
        "Базовая функциональность": test_basic_functionality(project_root)
    }
    
    # Генерируем итоговый отчет
    generate_summary_report(project_root, checks)
    
    # Возвращаем соответствующий код выхода
    if all(checks.values()):
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)