"""Обработчик для изображений."""

from typing import Any

import piexif
from PIL import Image

from metadata_cleaner.cleaner.errors import BackupError, MetadataProcessingError
from metadata_cleaner.cleaner.models import CleanResult, CleanStatus, FileJob

from . import BaseHandler

# Инициализация поддержки HEIF/HEIC форматов
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False


class ImageHandler(BaseHandler):
    """Обработчик для изображений."""

    def clean(self, job: FileJob) -> CleanResult:
        """Очистить метаданные из изображения."""
        try:
            # Создание бэкапа
            if not self._create_backup(job):
                msg = "Не удалось создать резервную копию"
                raise BackupError(msg)

            cleaned_fields = self._clean_image_metadata(job)

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

    def _clean_image_metadata(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из изображения."""
        cleaned_fields = {}
        extension = job.file_path.suffix.lower()

        if extension in [".jpg", ".jpeg"]:
            cleaned_fields = self._clean_jpeg_exif(job)
        elif extension == ".png":
            cleaned_fields = self._clean_png_metadata(job)
        elif extension in [".heic", ".heif"]:
            cleaned_fields = self._clean_heic_metadata(job)
        elif extension == ".gif":
            cleaned_fields = self._clean_gif_metadata(job)
        else:
            msg = f"Неподдерживаемый формат изображения: {extension}"
            raise MetadataProcessingError(msg)

        return cleaned_fields

    def _clean_jpeg_exif(self, job: FileJob) -> dict[str, Any]:
        """Очистить EXIF данные из JPEG файла."""
        cleaned_fields = {}

        try:
            # Чтение существующих EXIF данных
            exif_dict = piexif.load(str(job.file_path))

            # Сохранение удаляемых данных
            if job.clean_fields.get("camera", True):
                # Информация о камере
                if "0th" in exif_dict:
                    ifd = exif_dict["0th"]
                    if piexif.ImageIFD.Make in ifd:
                        # Безопасное декодирование с проверкой типа
                        make_value = ifd[piexif.ImageIFD.Make]
                        if isinstance(make_value, bytes):
                            cleaned_fields["camera_make"] = make_value.decode(
                                "utf-8", errors="ignore"
                            )
                        else:
                            cleaned_fields["camera_make"] = str(make_value)
                    if piexif.ImageIFD.Model in ifd:
                        model_value = ifd[piexif.ImageIFD.Model]
                        if isinstance(model_value, bytes):
                            cleaned_fields["camera_model"] = model_value.decode(
                                "utf-8", errors="ignore"
                            )
                        else:
                            cleaned_fields["camera_model"] = str(model_value)
                    if piexif.ImageIFD.Software in ifd:
                        software_value = ifd[piexif.ImageIFD.Software]
                        if isinstance(software_value, bytes):
                            cleaned_fields["software"] = software_value.decode(
                                "utf-8", errors="ignore"
                            )
                        else:
                            cleaned_fields["software"] = str(software_value)
                    
                    # Дополнительные персональные данные
                    if piexif.ImageIFD.Artist in ifd:
                        artist_value = ifd[piexif.ImageIFD.Artist]
                        if isinstance(artist_value, bytes):
                            cleaned_fields["artist"] = artist_value.decode("utf-8", errors="ignore")
                        else:
                            cleaned_fields["artist"] = str(artist_value)
                    
                    if piexif.ImageIFD.Copyright in ifd:
                        copyright_value = ifd[piexif.ImageIFD.Copyright]
                        if isinstance(copyright_value, bytes):
                            cleaned_fields["copyright"] = copyright_value.decode("utf-8", errors="ignore")
                        else:
                            cleaned_fields["copyright"] = str(copyright_value)

                # Дополнительная информация о камере из Exif IFD
                if "Exif" in exif_dict:
                    exif_ifd = exif_dict["Exif"]
                    if piexif.ExifIFD.CameraOwnerName in exif_ifd:
                        owner_value = exif_ifd[piexif.ExifIFD.CameraOwnerName]
                        if isinstance(owner_value, bytes):
                            cleaned_fields["camera_owner"] = owner_value.decode("utf-8", errors="ignore")
                        else:
                            cleaned_fields["camera_owner"] = str(owner_value)
                    
                    if piexif.ExifIFD.BodySerialNumber in exif_ifd:
                        body_serial = exif_ifd[piexif.ExifIFD.BodySerialNumber]
                        if isinstance(body_serial, bytes):
                            cleaned_fields["body_serial"] = body_serial.decode("utf-8", errors="ignore")
                        else:
                            cleaned_fields["body_serial"] = str(body_serial)
                    
                    if piexif.ExifIFD.LensSerialNumber in exif_ifd:
                        lens_serial = exif_ifd[piexif.ExifIFD.LensSerialNumber]
                        if isinstance(lens_serial, bytes):
                            cleaned_fields["lens_serial"] = lens_serial.decode("utf-8", errors="ignore")
                        else:
                            cleaned_fields["lens_serial"] = str(lens_serial)
                    
                    if piexif.ExifIFD.UserComment in exif_ifd:
                        user_comment = exif_ifd[piexif.ExifIFD.UserComment]
                        if isinstance(user_comment, bytes) and len(user_comment) > 8:
                            # UserComment начинается с 8-байтного заголовка кодировки
                            try:
                                cleaned_fields["user_comment"] = user_comment[8:].decode("utf-8", errors="ignore")
                            except:
                                cleaned_fields["user_comment"] = str(user_comment)

            if job.clean_fields.get("gps", True):
                # GPS данные
                if "GPS" in exif_dict and exif_dict["GPS"]:
                    cleaned_fields["gps_data"] = str(exif_dict["GPS"])

            if job.clean_fields.get("created", True):
                # Даты создания
                if "Exif" in exif_dict:
                    exif_ifd = exif_dict["Exif"]
                    if piexif.ExifIFD.DateTimeOriginal in exif_ifd:
                        cleaned_fields["date_original"] = exif_ifd[
                            piexif.ExifIFD.DateTimeOriginal
                        ].decode("utf-8")
                    if piexif.ExifIFD.DateTimeDigitized in exif_ifd:
                        cleaned_fields["date_digitized"] = exif_ifd[
                            piexif.ExifIFD.DateTimeDigitized
                        ].decode("utf-8")

            # Создание новых EXIF данных без указанных полей
            new_exif_dict = {
                "0th": {},
                "Exif": {},
                "1st": {},
                "thumbnail": None,
                "GPS": {},
            }

            # Копирование только тех данных, которые нужно оставить
            if "0th" in exif_dict:
                for tag, value in exif_dict["0th"].items():
                    # Оставляем основную информацию об изображении
                    if tag in [
                        piexif.ImageIFD.ImageWidth,
                        piexif.ImageIFD.ImageLength,
                        piexif.ImageIFD.Orientation,
                        piexif.ImageIFD.XResolution,
                        piexif.ImageIFD.YResolution,
                        piexif.ImageIFD.ResolutionUnit,
                    ]:
                        new_exif_dict["0th"][tag] = value
                    # Камера и персональные данные - удаляем если указано
                    elif not job.clean_fields.get("camera", True) and tag in [
                        piexif.ImageIFD.Make,
                        piexif.ImageIFD.Model,
                        piexif.ImageIFD.Software,
                        piexif.ImageIFD.Artist,
                        piexif.ImageIFD.Copyright,
                    ]:
                        new_exif_dict["0th"][tag] = value

            if "Exif" in exif_dict:
                for tag, value in exif_dict["Exif"].items():
                    # Оставляем технические параметры съемки
                    if tag in [
                        piexif.ExifIFD.ExposureTime,
                        piexif.ExifIFD.FNumber,
                        piexif.ExifIFD.ISOSpeedRatings,
                        piexif.ExifIFD.FocalLength,
                    ]:
                        new_exif_dict["Exif"][tag] = value
                    # Даты и персональные данные камеры - оставляем если не нужно удалять
                    elif not job.clean_fields.get("created", True) and tag in [
                        piexif.ExifIFD.DateTimeOriginal,
                        piexif.ExifIFD.DateTimeDigitized,
                    ]:
                        new_exif_dict["Exif"][tag] = value
                    elif not job.clean_fields.get("camera", True) and tag in [
                        piexif.ExifIFD.CameraOwnerName,
                        piexif.ExifIFD.BodySerialNumber,
                        piexif.ExifIFD.LensSerialNumber,
                        piexif.ExifIFD.UserComment,
                    ]:
                        new_exif_dict["Exif"][tag] = value

            # GPS данные - не копируем если нужно удалить
            if not job.clean_fields.get("gps", True) and "GPS" in exif_dict:
                new_exif_dict["GPS"] = exif_dict["GPS"]

            # Открытие изображения и сохранение с новыми EXIF
            img = Image.open(str(job.file_path))

            # Создание байтов EXIF
            exif_bytes = piexif.dump(new_exif_dict)

            # Сохранение изображения с сохранением ICC профиля
            output_path = job.output_path or job.file_path
            save_kwargs = {"exif": exif_bytes, "quality": 95, "optimize": True}

            # Сохранение ICC профиля если он есть
            if hasattr(img, "info") and "icc_profile" in img.info:
                save_kwargs["icc_profile"] = img.info["icc_profile"]

            img.save(str(output_path), **save_kwargs)

        except piexif.InvalidImageDataError:
            # Если EXIF данных нет, просто копируем изображение
            img = Image.open(str(job.file_path))
            output_path = job.output_path or job.file_path
            img.save(str(output_path), quality=95)

        return cleaned_fields

    def _clean_png_metadata(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из PNG файла."""
        cleaned_fields = {}

        # Открытие изображения
        img = Image.open(str(job.file_path))

        # Сохранение метаданных, которые будут удалены
        if hasattr(img, "info") and img.info:
            for key, value in img.info.items():
                if isinstance(value, str | bytes):
                    cleaned_fields[f"png_{key}"] = str(value)

        # Создание нового изображения без метаданных
        new_img = Image.new(img.mode, img.size)
        new_img.putdata(list(img.getdata()))

        # Сохранение без метаданных
        output_path = job.output_path or job.file_path
        new_img.save(str(output_path), format="PNG")

        return cleaned_fields

    def _clean_heic_metadata(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из HEIC файла."""
        cleaned_fields = {}
        
        if not HEIF_AVAILABLE:
            msg = "Для работы с HEIC требуется pillow-heif. Установите зависимость."
            raise MetadataProcessingError(msg)

        try:
            # Открываем HEIC изображение
            img = Image.open(str(job.file_path))

            # Сохраняем удаляемые метаданные
            if hasattr(img, "info") and img.info:
                for key, value in img.info.items():
                    if key not in ['icc_profile']:  # Сохраняем ICC профиль
                        cleaned_fields[f"heic_{key}"] = str(value)

            # Создаём новое изображение без метаданных
            new_img = Image.new(img.mode, img.size)
            new_img.putdata(list(img.getdata()))
            
            # Сохраняем ICC профиль если он есть
            if hasattr(img, "info") and 'icc_profile' in img.info:
                new_img.info['icc_profile'] = img.info['icc_profile']

            output_path = job.output_path or job.file_path
            
            # Пытаемся сохранить как HEIC
            try:
                new_img.save(str(output_path), format="HEIF", quality=95)
            except (ValueError, OSError):
                # Если не получается сохранить как HEIC, пробуем другие варианты
                try:
                    # Пробуем AVIF как альтернативу
                    new_img.save(str(output_path), format="AVIF", quality=95)
                except (ValueError, OSError):
                    # В крайнем случае сохраняем как высококачественный JPEG
                    if str(output_path).lower().endswith('.heic'):
                        output_path = output_path.with_suffix('.jpg')
                    new_img.save(str(output_path), format="JPEG", quality=98, optimize=True)
                    cleaned_fields["format_changed"] = "HEIC → JPEG (высокое качество)"

        except Exception as e:
            msg = f"Ошибка обработки HEIC: {e!s}"
            raise MetadataProcessingError(msg)
            
        return cleaned_fields

    def _clean_gif_metadata(self, job: FileJob) -> dict[str, Any]:
        """Очистить метаданные из GIF файла."""
        cleaned_fields = {}

        # Открытие GIF
        img = Image.open(str(job.file_path))

        # Сохранение информации о метаданных
        if hasattr(img, "info") and img.info:
            for key, value in img.info.items():
                if isinstance(value, str | bytes):
                    cleaned_fields[f"gif_{key}"] = str(value)

        # Сохранение GIF без метаданных
        output_path = job.output_path or job.file_path

        # Для анимированных GIF нужна особая обработка
        frames = []
        try:
            while True:
                frames.append(img.copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        if len(frames) > 1:
            # Анимированный GIF
            frames[0].save(
                str(output_path), save_all=True, append_images=frames[1:], format="GIF"
            )
        else:
            # Статичный GIF
            img.save(str(output_path), format="GIF")

        return cleaned_fields
