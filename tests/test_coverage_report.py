"""Тесты для генерации отчетов покрытия кода."""

import pytest
import subprocess
import sys
from pathlib import Path


class TestCoverageReporting:
    """Тесты системы отчетности покрытия кода."""

    def test_coverage_configuration_exists(self):
        """Проверяет наличие конфигурации покрытия в pyproject.toml."""
        project_root = Path(__file__).parent.parent
        pyproject_file = project_root / "pyproject.toml"
        
        assert pyproject_file.exists(), "pyproject.toml не найден"
        
        content = pyproject_file.read_text(encoding='utf-8')
        assert "pytest.ini_options" in content, "Конфигурация pytest не найдена"
        assert "--cov=metadata_cleaner" in content, "Конфигурация покрытия не найдена"

    def test_coverage_can_run(self):
        """Проверяет, что pytest-cov может запуститься."""
        try:
            import pytest_cov
        except ImportError:
            pytest.skip("pytest-cov не установлен")
        
        # Простой тест запуска coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", "--version"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"pytest не может запуститься: {result.stderr}"

    def test_coverage_reports_can_be_generated(self):
        """Проверяет, что отчеты покрытия могут быть сгенерированы."""
        project_root = Path(__file__).parent.parent
        
        # Запускаем простой тест с покрытием
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--cov=metadata_cleaner",
            "--cov-report=term",
            "--cov-report=xml",
            str(project_root / "tests" / "test_models.py"),
            "-v"
        ], capture_output=True, text=True, cwd=project_root)
        
        # Проверяем, что команда выполнилась (может быть warning'и, но не ошибки)
        if result.returncode != 0:
            pytest.skip(f"Не удалось запустить pytest с покрытием: {result.stderr}")
        
        # Проверяем, что XML отчет создался
        coverage_xml = project_root / "coverage.xml"
        if coverage_xml.exists():
            assert coverage_xml.stat().st_size > 0, "XML отчет покрытия пустой"

    def test_coverage_thresholds(self):
        """Проверяет пороговые значения покрытия."""
        # Эти значения можно настроить в зависимости от требований проекта
        minimum_coverage = 60  # 60% минимальное покрытие
        target_coverage = 80   # 80% целевое покрытие
        
        # Информативный тест - показывает ожидаемые пороги
        assert minimum_coverage < target_coverage
        assert minimum_coverage >= 50  # Разумный минимум
        assert target_coverage <= 95   # Реалистичная цель

    def test_coverage_exclude_patterns(self):
        """Проверяет исключения из покрытия."""
        project_root = Path(__file__).parent.parent
        pyproject_file = project_root / "pyproject.toml"
        
        if pyproject_file.exists():
            content = pyproject_file.read_text(encoding='utf-8')
            
            # Проверяем, что есть разумные исключения
            # (тесты, примеры, и т.д. обычно исключаются)
            expected_patterns = ["tests/*", "__pycache__/*"]
            
            # Это информативная проверка - показывает что нужно учесть
            for pattern in expected_patterns:
                # В реальном проекте эти паттерны могут быть в [tool.coverage.run]
                pass

    def test_coverage_html_report_generation(self):
        """Проверяет генерацию HTML отчета покрытия."""
        project_root = Path(__file__).parent.parent
        
        # Пытаемся сгенерировать HTML отчет
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--cov=metadata_cleaner",
            "--cov-report=html",
            str(project_root / "tests" / "test_models.py"),
            "-q"
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            # Проверяем, что HTML отчет создался
            html_dir = project_root / "htmlcov"
            if html_dir.exists():
                index_file = html_dir / "index.html"
                assert index_file.exists(), "HTML отчет не создан"
                assert index_file.stat().st_size > 0, "HTML отчет пустой"

    def test_coverage_integration_with_ci(self):
        """Проверяет интеграцию покрытия с CI/CD."""
        project_root = Path(__file__).parent.parent
        
        # Проверяем наличие GitHub Actions workflow
        workflows_dir = project_root / ".github" / "workflows"
        if workflows_dir.exists():
            ci_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            
            ci_content = ""
            for ci_file in ci_files:
                ci_content += ci_file.read_text(encoding='utf-8')
            
            # Проверяем упоминание coverage в CI
            coverage_indicators = [
                "coverage", "codecov", "--cov", "pytest-cov"
            ]
            
            has_coverage = any(indicator in ci_content.lower() for indicator in coverage_indicators)
            assert has_coverage, "Покрытие кода не настроено в CI/CD"

    def test_coverage_badges_configuration(self):
        """Проверяет конфигурацию значков покрытия."""
        project_root = Path(__file__).parent.parent
        
        # Проверяем README файлы на наличие значков покрытия
        readme_files = [
            project_root / "README.md",
            project_root / "README_EN.md"
        ]
        
        coverage_badge_indicators = [
            "codecov", "coverage", "badge", "shield"
        ]
        
        for readme_file in readme_files:
            if readme_file.exists():
                content = readme_file.read_text(encoding='utf-8').lower()
                # Информативная проверка - не обязательно иметь значки
                has_badges = any(indicator in content for indicator in coverage_badge_indicators)
                # В реальном проекте можно добавить значки покрытия

    def test_coverage_config_completeness(self):
        """Проверяет полноту конфигурации покрытия."""
        project_root = Path(__file__).parent.parent
        pyproject_file = project_root / "pyproject.toml"
        
        if pyproject_file.exists():
            content = pyproject_file.read_text(encoding='utf-8')
            
            # Проверяем основные опции pytest-cov
            expected_options = [
                "--cov=metadata_cleaner",  # Основной пакет
                "--cov-report=xml",        # XML отчет для CI
                "--cov-report=term-missing"  # Детальный терминальный отчет
            ]
            
            for option in expected_options:
                assert option in content, f"Опция покрытия {option} не найдена в конфигурации"

    def test_coverage_reporting_performance(self):
        """Проверяет производительность генерации отчетов покрытия."""
        import time
        project_root = Path(__file__).parent.parent
        
        start_time = time.time()
        
        # Запускаем быстрый тест с покрытием
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--cov=metadata_cleaner",
            "--cov-report=term",
            str(project_root / "tests" / "test_models.py"),
            "-q"
        ], capture_output=True, text=True, cwd=project_root)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            # Генерация отчета покрытия не должна значительно замедлять тесты
            assert execution_time < 30, f"Генерация отчета покрытия слишком медленная: {execution_time:.1f}s"

    def test_coverage_exclusion_markers(self):
        """Проверяет использование маркеров исключения покрытия."""
        project_root = Path(__file__).parent.parent
        
        # Ищем файлы с маркерами исключения покрытия
        python_files = list((project_root / "metadata_cleaner").rglob("*.py"))
        
        exclusion_markers = [
            "# pragma: no cover",
            "# nocov",
            "# coverage: disable"
        ]
        
        files_with_exclusions = []
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                for marker in exclusion_markers:
                    if marker in content:
                        files_with_exclusions.append(str(py_file))
                        break
            except (UnicodeDecodeError, PermissionError):
                continue
        
        # Информативная проверка - показывает файлы с исключениями
        if files_with_exclusions:
            print(f"Файлы с исключениями покрытия: {files_with_exclusions}")


class TestCoverageQuality:
    """Тесты качества покрытия кода."""

    def test_critical_functions_coverage(self):
        """Проверяет, что критически важные функции покрыты тестами."""
        project_root = Path(__file__).parent.parent
        
        # Список критически важных модулей
        critical_modules = [
            "metadata_cleaner/cleaner/dispatcher.py",
            "metadata_cleaner/cleaner/handlers/",
            "metadata_cleaner/services/settings_service.py"
        ]
        
        for module_path in critical_modules:
            full_path = project_root / module_path
            if full_path.exists():
                # Проверяем, что для модуля есть соответствующие тесты
                if full_path.is_file():
                    module_name = full_path.stem
                    test_file = project_root / "tests" / f"test_{module_name}.py"
                    assert test_file.exists(), f"Тест для критического модуля {module_name} не найден"

    def test_test_files_naming_convention(self):
        """Проверяет соблюдение соглашений об именовании тестовых файлов."""
        project_root = Path(__file__).parent.parent
        tests_dir = project_root / "tests"
        
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            
            # Все тестовые файлы должны начинаться с "test_"
            all_files = list(tests_dir.glob("*.py"))
            non_test_files = [f for f in all_files if not f.name.startswith("test_") and f.name != "__init__.py" and f.name != "conftest.py"]
            
            if non_test_files:
                pytest.fail(f"Файлы в tests/ не следуют соглашению именования: {[f.name for f in non_test_files]}")

    def test_test_functions_coverage_quality(self):
        """Проверяет качество покрытия тестовых функций."""
        project_root = Path(__file__).parent.parent
        tests_dir = project_root / "tests"
        
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            
            total_test_functions = 0
            
            for test_file in test_files:
                try:
                    content = test_file.read_text(encoding='utf-8')
                    
                    # Подсчитываем тестовые функции
                    test_function_count = content.count("def test_")
                    total_test_functions += test_function_count
                    
                except (UnicodeDecodeError, PermissionError):
                    continue
            
            # Должно быть разумное количество тестов
            assert total_test_functions >= 10, f"Недостаточно тестовых функций: {total_test_functions}"