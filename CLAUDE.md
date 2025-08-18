# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Metadata Cleaner is a desktop application built with Python and Flet for removing metadata from various file formats (images, documents, PDFs, videos). The app supports local processing with no data transmission, automatic backups, and selective metadata cleaning.

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Install development dependencies
poetry install --with dev
```

### Running the Application
```bash
# Run GUI application
python run.py
# or
poetry run metadata-cleaner

# Run CLI version
poetry run metadata-cleaner-cli
```

### Testing
```bash
# Run all tests with coverage
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=metadata_cleaner --cov-report=xml --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_dispatcher.py
```

### Code Quality
```bash
# Format code with black
poetry run black .

# Lint with ruff
poetry run ruff check .

# Auto-fix linting issues
poetry run ruff check . --fix

# Type checking (if mypy is added)
poetry run mypy metadata_cleaner/
```

### Building
```bash
# Build for current platform
python build.py

# The build script automatically:
# - Downloads FFmpeg binaries for video processing
# - Creates executables with PyInstaller
# - Handles platform-specific configurations
```

## Architecture

### Core Components

**Dispatcher System**: `metadata_cleaner/cleaner/dispatcher.py`
- Routes files to appropriate handlers based on file type
- Manages processing workflow and settings integration
- Handles file type detection and validation

**File Handlers**: `metadata_cleaner/cleaner/handlers/`
- `image.py`: EXIF, IPTC, XMP metadata for JPG, PNG, GIF, HEIC, HEIF
- `pdf.py`: Document properties and metadata for PDF files
- `office.py`: Metadata for DOCX, XLSX, PPTX files
- `video.py`: Video metadata using FFmpeg for MP4, MOV files

**Models**: `metadata_cleaner/cleaner/models.py`
- Data structures for file processing (FileJob, CleanResult, CleanStatus)
- Enums for file types and output modes
- Metadata field definitions for each file type

**GUI Framework**: `metadata_cleaner/gui/`
- Flet-based Material Design 3 interface
- Component-based architecture in `components/`
- Localization support (Russian/English)
- Settings persistence and theme management

**Services**: `metadata_cleaner/services/`
- `settings_service.py`: Configuration management and persistence

### Key Libraries
- **Flet**: Cross-platform UI framework (Flutter-based)
- **Pillow + piexif**: Image processing and EXIF data
- **python-docx, openpyxl, python-pptx**: Office document handling
- **PyPDF**: PDF metadata processing
- **FFmpeg**: Video file metadata handling (bundled binary)
- **hachoir**: General metadata extraction
- **pillow-heif**: HEIC/HEIF image support

### File Processing Workflow
1. File type detection based on extension
2. Route to appropriate handler
3. Extract existing metadata
4. Apply cleaning rules based on user settings
5. Create backup if enabled
6. Write cleaned file
7. Return processing results

### Settings and Configuration
- Settings stored in JSON format via SettingsService
- Supports different output modes: replace, create copy, backup and overwrite
- Configurable metadata cleaning profiles per file type
- Theme and localization preferences

### Error Handling
- Custom exceptions in `errors.py`
- Graceful degradation for unsupported files
- Comprehensive error reporting in processing results

## Testing
- Test files in `tests/test_files/` cover all supported formats
- Unit tests for handlers, dispatcher, models, and services
- Integration tests for end-to-end file processing workflows
- GitHub Actions CI/CD with automated testing

## Build System
- Poetry for dependency management
- PyInstaller for creating standalone executables
- Cross-platform build script (`build.py`) with FFmpeg integration
- Automated release workflows in `.github/workflows/`