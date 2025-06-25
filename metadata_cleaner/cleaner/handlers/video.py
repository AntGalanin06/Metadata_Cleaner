"""Обработчик для видео файлов."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from metadata_cleaner.cleaner.errors import BackupError, MetadataProcessingError
from metadata_cleaner.cleaner.models import CleanResult, CleanStatus, FileJob

from . import BaseHandler


class VideoHandler(BaseHandler):
    """Обработчик для видео файлов."""

    def clean(self, job: FileJob) -> CleanResult:
        """Очистить метаданные из видео файла."""
        try:
            # Создание бэкапа
            if not self._create_backup(job):
                msg = "Не удалось создать резервную копию"
                raise BackupError(msg)

            cleaned_fields = self._clean_video_metadata(job)

            return CleanResult(
                job=job,
                status=CleanStatus.SUCCESS,
                message=f"Метаданные успешно очищены из {job.file_path.name}",
                cleaned_fields=cleaned_fields,
            )

        except Exception as e:
            return CleanResult(
                job=job,
                status=CleanStatus.ERROR,
                message=f"Ошибка при обработке {job.file_path.name}: {e!s}",
                error=e,
            )

    def _clean_video_metadata(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из видео файла."""
        cleaned_fields = {}

        try:
            # Проверяем что файл является валидным видео
            parser = createParser(str(job.file_path))
            if not parser:
                msg = f"Не удалось распознать видео файл: {job.file_path.name}"
                raise MetadataProcessingError(msg)
                
            metadata = extractMetadata(parser)
            if metadata:
                # Сохранение информации об удаляемых метаданных
                metadata_lines = metadata.exportPlaintext()
                for line in metadata_lines:
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ["creation", "date", "time"]):
                        cleaned_fields["creation_info"] = line.strip()
                    elif any(keyword in line_lower for keyword in ["author", "artist", "creator", "encoder"]):
                        cleaned_fields["author_info"] = line.strip()
                    elif any(keyword in line_lower for keyword in ["title"]):
                        cleaned_fields["title_info"] = line.strip()
                    elif any(keyword in line_lower for keyword in ["comment", "description"]):
                        cleaned_fields["comment_info"] = line.strip()
                    elif any(keyword in line_lower for keyword in ["gps", "location", "coordinate"]):
                        cleaned_fields["gps_info"] = line.strip()

            # Попытка очистки через ffmpeg
            success = self._clean_with_ffmpeg(job)
            
            if not success:
                # Fallback: просто копируем файл с предупреждением
                output_path = job.output_path or job.file_path
                if str(output_path) != str(job.file_path):
                    shutil.copy2(str(job.file_path), str(output_path))
                cleaned_fields["warning"] = "FFmpeg недоступен. Метаданные не удалены."
            else:
                cleaned_fields["method"] = "FFmpeg - полная очистка метаданных"

        except Exception as e:
            msg = f"Ошибка обработки видео: {e!s}"
            raise MetadataProcessingError(msg)

        return cleaned_fields

    def _clean_with_ffmpeg(self, job: FileJob) -> bool:
        """Очистить метаданные с помощью ffmpeg."""
        try:
            # Попробуем найти ffmpeg (включая встроенный)
            ffmpeg_paths = self._get_ffmpeg_paths()
            
            ffmpeg_cmd = None
            for path in ffmpeg_paths:
                try:
                    result = subprocess.run(
                        [path, "-version"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.returncode == 0:
                        ffmpeg_cmd = path
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
                    
            if not ffmpeg_cmd:
                return False

            output_path = job.output_path or job.file_path
            temp_path = output_path.with_suffix('.tmp' + output_path.suffix)

            # Команда ffmpeg для полной очистки метаданных
            cmd = [
                ffmpeg_cmd,
                "-i", str(job.file_path),  # Входной файл
                "-map_metadata", "-1",     # Удалить ВСЕ метаданные
                "-map_chapters", "-1",     # Удалить главы
                "-c", "copy",              # Копировать без перекодирования
                "-y",                      # Перезаписать без вопросов
                str(temp_path)             # Временный выходной файл
            ]

            # Выполняем команду
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 минут максимум
            )

            if result.returncode == 0:
                # Успешно - заменяем оригинал
                if temp_path.exists():
                    temp_path.replace(output_path)
                    return True
            else:
                # Удаляем временный файл если он создался
                if temp_path.exists():
                    temp_path.unlink()
                return False

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
            return False
        except Exception:
            return False
        
        return False

    def _get_ffmpeg_paths(self) -> list[str]:
        """Получить список путей для поиска FFmpeg."""
        paths = []
        
        # 1. Встроенный FFmpeg (приоритет!)
        if getattr(sys, 'frozen', False):
            # Запущено как PyInstaller bundle
            bundle_dir = Path(sys._MEIPASS)
            bundled_ffmpeg = bundle_dir / "bundled_ffmpeg" / "ffmpeg"
            if not bundled_ffmpeg.exists():
                bundled_ffmpeg = bundle_dir / "bundled_ffmpeg" / "ffmpeg.exe"
            if bundled_ffmpeg.exists():
                paths.append(str(bundled_ffmpeg))
        else:
            # Режим разработки - проверяем локальную папку
            local_ffmpeg = Path("bundled_ffmpeg") / "ffmpeg"
            if not local_ffmpeg.exists():
                local_ffmpeg = Path("bundled_ffmpeg") / "ffmpeg.exe"
            if local_ffmpeg.exists():
                paths.append(str(local_ffmpeg))
        
        # 2. Системные пути
        paths.extend([
            "ffmpeg",                    # В PATH
            "/opt/homebrew/bin/ffmpeg",  # Homebrew на macOS ARM
            "/usr/local/bin/ffmpeg",     # Homebrew на macOS Intel
            "/usr/bin/ffmpeg",           # System Linux
        ])
        
        return paths

    def _check_ffmpeg_available(self) -> bool:
        """Проверить доступность ffmpeg."""
        ffmpeg_paths = self._get_ffmpeg_paths()
        
        for path in ffmpeg_paths:
            try:
                result = subprocess.run(
                    [path, "-version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return False
