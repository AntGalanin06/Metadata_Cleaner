# Makefile для проекта Metadata Cleaner
.PHONY: help install test test-unit test-integration test-performance test-coverage \
        test-html test-quick lint format type-check build clean coverage-report \
        ci pre-commit install-dev docs

# Переменные
PYTHON := python
POETRY := poetry
PROJECT_NAME := metadata_cleaner
TESTS_DIR := tests
SRC_DIR := metadata_cleaner

# Цвета для вывода
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

help: ## Показать эту справку
	@echo "$(BLUE)🧪 Metadata Cleaner - Команды разработки$(NC)"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	$(POETRY) install

install-dev: ## Установить зависимости для разработки
	@echo "$(BLUE)🛠️ Установка зависимостей для разработки...$(NC)"
	$(POETRY) install --with dev

# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================

test: ## Запустить все тесты
	@echo "$(BLUE)🧪 Запуск всех тестов...$(NC)"
	$(PYTHON) scripts/run_tests.py --all

test-unit: ## Запустить unit тесты
	@echo "$(BLUE)🔬 Запуск unit тестов...$(NC)"
	$(PYTHON) scripts/run_tests.py --unit

test-integration: ## Запустить интеграционные тесты
	@echo "$(BLUE)🔗 Запуск интеграционных тестов...$(NC)"
	$(PYTHON) scripts/run_tests.py --integration

test-performance: ## Запустить тесты производительности
	@echo "$(BLUE)⚡ Запуск тестов производительности...$(NC)"
	$(PYTHON) scripts/run_tests.py --performance

test-quick: ## Запустить быстрые тесты (исключая медленные)
	@echo "$(BLUE)🚀 Запуск быстрых тестов...$(NC)"
	$(PYTHON) scripts/run_tests.py --quick

test-coverage: ## Запустить тесты с отчетом покрытия
	@echo "$(BLUE)📊 Запуск тестов с покрытием кода...$(NC)"
	$(PYTHON) scripts/run_tests.py --all --coverage

test-html: ## Генерировать HTML отчет покрытия
	@echo "$(BLUE)🌐 Генерация HTML отчета покрытия...$(NC)"
	$(PYTHON) scripts/run_tests.py --all --html
	@echo "$(GREEN)✅ HTML отчет: file://$(PWD)/htmlcov/index.html$(NC)"

test-watch: ## Запуск тестов в режиме наблюдения
	@echo "$(BLUE)👀 Запуск тестов в режиме наблюдения...$(NC)"
	$(POETRY) run ptw --runner "$(PYTHON) -m pytest"

# ============================================================================
# КАЧЕСТВО КОДА
# ============================================================================

lint: ## Проверка кода с ruff
	@echo "$(BLUE)🔍 Линтинг кода...$(NC)"
	$(POETRY) run ruff check $(SRC_DIR) $(TESTS_DIR)

lint-fix: ## Автоматическое исправление ошибок линтинга
	@echo "$(BLUE)🔧 Автоматическое исправление линтинга...$(NC)"
	$(POETRY) run ruff check --fix $(SRC_DIR) $(TESTS_DIR)

format: ## Форматирование кода с black
	@echo "$(BLUE)✨ Форматирование кода...$(NC)"
	$(POETRY) run black $(SRC_DIR) $(TESTS_DIR)

format-check: ## Проверка форматирования без изменений
	@echo "$(BLUE)📋 Проверка форматирования...$(NC)"
	$(POETRY) run black --check --diff $(SRC_DIR) $(TESTS_DIR)

type-check: ## Проверка типов с mypy
	@echo "$(BLUE)🎯 Проверка типов...$(NC)"
	$(POETRY) run mypy $(SRC_DIR) --ignore-missing-imports || true

security: ## Проверка безопасности с bandit
	@echo "$(BLUE)🔒 Проверка безопасности...$(NC)"
	$(POETRY) run bandit -r $(SRC_DIR) -f json -o security-report.json || true
	$(POETRY) run bandit -r $(SRC_DIR) || true

quality: lint format-check type-check security ## Полная проверка качества кода

# ============================================================================
# СБОРКА И РАЗВЕРТЫВАНИЕ
# ============================================================================

build: ## Сборка приложения
	@echo "$(BLUE)🏗️ Сборка приложения...$(NC)"
	$(PYTHON) build.py --verbose

build-clean: ## Чистая сборка приложения
	@echo "$(BLUE)🧹 Чистая сборка приложения...$(NC)"
	$(PYTHON) build.py --clean --verbose

installers: ## Создание инсталляторов
	@echo "$(BLUE)📦 Создание инсталляторов...$(NC)"
	./installers/build_all.sh

installers-linux: ## Создание Linux инсталляторов
	@echo "$(BLUE)🐧 Создание Linux инсталляторов...$(NC)"
	./installers/build_all.sh linux

installers-windows: ## Создание Windows инсталлятора
	@echo "$(BLUE)🪟 Создание Windows инсталлятора...$(NC)"
	./installers/build_all.sh windows

installers-macos: ## Создание macOS инсталлятора
	@echo "$(BLUE)🍎 Создание macOS инсталлятора...$(NC)"
	./installers/build_all.sh macos

# ============================================================================
# ОЧИСТКА
# ============================================================================

clean: ## Очистка временных файлов
	@echo "$(BLUE)🧹 Очистка временных файлов...$(NC)"
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf coverage.json
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-all: clean ## Полная очистка включая виртуальное окружение
	@echo "$(BLUE)💥 Полная очистка...$(NC)"
	rm -rf .venv/

# ============================================================================
# ОТЧЕТЫ И АНАЛИЗ
# ============================================================================

coverage-report: ## Детальный отчет покрытия
	@echo "$(BLUE)📊 Генерация отчета покрытия...$(NC)"
	$(POETRY) run pytest --cov=$(SRC_DIR) --cov-report=html --cov-report=xml --cov-report=term-missing $(TESTS_DIR)
	@echo "$(GREEN)✅ HTML отчет: file://$(PWD)/htmlcov/index.html$(NC)"
	@echo "$(GREEN)✅ XML отчет: $(PWD)/coverage.xml$(NC)"

metrics: ## Метрики кода
	@echo "$(BLUE)📈 Анализ метрик кода...$(NC)"
	@echo "$(YELLOW)Количество строк кода:$(NC)"
	@find $(SRC_DIR) -name "*.py" -exec wc -l {} + | tail -1
	@echo "$(YELLOW)Количество тестовых файлов:$(NC)"
	@find $(TESTS_DIR) -name "test_*.py" | wc -l
	@echo "$(YELLOW)Общее количество тестов:$(NC)"
	@grep -r "def test_" $(TESTS_DIR) | wc -l

dependency-check: ## Проверка зависимостей на безопасность
	@echo "$(BLUE)🔍 Проверка зависимостей...$(NC)"
	$(POETRY) run safety check || true

# ============================================================================
# CI/CD И АВТОМАТИЗАЦИЯ
# ============================================================================

ci: ## Запуск полного CI pipeline
	@echo "$(BLUE)🤖 Запуск CI pipeline...$(NC)"
	$(MAKE) quality
	$(PYTHON) scripts/run_tests.py --ci
	@echo "$(GREEN)✅ CI pipeline завершен$(NC)"

pre-commit: ## Запуск pre-commit хуков
	@echo "$(BLUE)🎣 Запуск pre-commit хуков...$(NC)"
	$(POETRY) run pre-commit run --all-files

pre-commit-install: ## Установка pre-commit хуков
	@echo "$(BLUE)⚙️ Установка pre-commit хуков...$(NC)"
	$(POETRY) run pre-commit install

# ============================================================================
# РАЗРАБОТКА
# ============================================================================

dev-setup: install-dev pre-commit-install ## Настройка среды разработки
	@echo "$(GREEN)✅ Среда разработки настроена$(NC)"

run-gui: ## Запуск GUI приложения
	@echo "$(BLUE)🖥️ Запуск GUI приложения...$(NC)"
	$(POETRY) run python run.py

run-cli: ## Запуск CLI приложения
	@echo "$(BLUE)💻 Запуск CLI приложения...$(NC)"
	$(POETRY) run metadata-cleaner-cli --help

# ============================================================================
# ДОКУМЕНТАЦИЯ
# ============================================================================

docs: ## Генерация документации
	@echo "$(BLUE)📚 Генерация документации...$(NC)"
	@echo "$(YELLOW)Документация будет доступна в docs/$(NC)"

docs-serve: ## Запуск локального сервера документации
	@echo "$(BLUE)🌐 Запуск сервера документации...$(NC)"
	@echo "$(YELLOW)Функция в разработке$(NC)"

# ============================================================================
# УТИЛИТЫ
# ============================================================================

version: ## Показать версию
	@echo "$(BLUE)📋 Информация о версии:$(NC)"
	@$(POETRY) version
	@$(PYTHON) -c "from metadata_cleaner.version import __version__; print(f'App version: {__version__}')"

info: ## Показать информацию о проекте
	@echo "$(BLUE)ℹ️ Информация о проекте:$(NC)"
	@echo "Название: $(PROJECT_NAME)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Poetry: $(shell $(POETRY) --version)"
	@echo "Исходный код: $(SRC_DIR)/"
	@echo "Тесты: $(TESTS_DIR)/"

# Настройка по умолчанию
.DEFAULT_GOAL := help