"""Тесты для CLI интерфейса."""

import pytest
import subprocess
from unittest.mock import patch
import sys
from pathlib import Path
import tempfile

from metadata_cleaner.cli import main
from metadata_cleaner.cleaner.models import (
    CleanStatus,
    CleanResult,
    FileJob,
)


@pytest.mark.unit
class TestCLI:
    """Тесты CLI."""

    def test_main_no_args(self):
        """Тест запуска без аргументов."""
        expected_missing_args_exit_code = 2
        
        with patch("sys.argv", ["metadata_cleaner"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Должен завершиться с ошибкой из-за отсутствия обязательных аргументов
            assert exc_info.value.code == expected_missing_args_exit_code

    def test_main_help(self):
        """Тест показа справки."""
        with patch("sys.argv", ["metadata_cleaner", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_version(self):
        """Тест показа версии."""
        with patch("sys.argv", ["metadata_cleaner", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_with_nonexistent_file(self):
        """Тест с несуществующим файлом."""
        with patch("sys.argv", ["metadata_cleaner", "/nonexistent/file.jpg"]), \
             patch("metadata_cleaner.cli.MetadataDispatcher") as mock_dispatcher:
            mock_dispatcher.return_value.clean_file.return_value = {
                "status": "error",
                "message": "File not found",
            }
            result = main()
            # Должен завершиться с ошибкой
            assert result != 0

    def test_main_with_valid_arguments(self):
        """Тест с валидными аргументами."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Создаем временный файл
            temp_path.write_bytes(b"fake jpeg data")

            with patch("sys.argv", ["metadata_cleaner", str(temp_path)]), \
                 patch("metadata_cleaner.cli.MetadataDispatcher") as mock_dispatcher_class:
                mock_dispatcher = mock_dispatcher_class.return_value
                # Мокаем методы как они используются в CLI
                mock_dispatcher.is_supported.return_value = True

                # Создаем успешный результат
                job = FileJob(file_path=Path(str(temp_path)))
                mock_result = CleanResult(
                    job=job, status=CleanStatus.SUCCESS, message="Success"
                )
                mock_dispatcher.process_file_with_options.return_value = mock_result

                result = main()
                # Должен завершиться успешно
                assert result == 0
        finally:
            # Удаляем временный файл
            if temp_path.exists():
                temp_path.unlink()


@pytest.mark.integration
class TestCLIIntegration:
    """Интеграционные тесты CLI."""

    def test_cli_integration_help(self):
        """Интеграционный тест справки."""
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-c",
                'from metadata_cleaner.cli import main; import sys; sys.argv = ["test", "--help"]; main()',
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Справка должна содержать основные опции
        assert "--keep-author" in result.stdout or "--keep-dates" in result.stdout

    def test_cli_error_handling(self):
        """Тест обработки ошибок CLI."""
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-c",
                'from metadata_cleaner.cli import main; import sys; sys.argv = ["test", "/invalid/path"]; exit_code = main(); sys.exit(exit_code)',
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Должен завершиться с ошибкой
        assert result.returncode != 0
