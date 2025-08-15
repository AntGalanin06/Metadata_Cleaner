"""Тесты для реестра метаданных."""

import pytest
from metadata_cleaner.cleaner.metadata_registry import MetadataRegistry, MetadataField, MetadataCategory


class TestMetadataRegistry:
    """Тесты класса MetadataRegistry."""

    def test_get_supported_file_types(self):
        """Тест получения поддерживаемых типов файлов."""
        supported_types = MetadataRegistry.get_supported_file_types()
        
        # Проверяем, что возвращается список
        assert isinstance(supported_types, list)
        
        # Проверяем наличие основных типов файлов
        expected_types = ['image', 'document', 'pdf', 'video']
        assert set(expected_types) == set(supported_types)

    def test_get_fields_for_image_type(self):
        """Тест получения полей для изображений."""
        fields = MetadataRegistry.get_fields_for_file_type('image')
        
        # Проверяем, что возвращается список MetadataField
        assert isinstance(fields, list)
        assert all(isinstance(field, MetadataField) for field in fields)
        
        # Проверяем наличие основных полей для изображений
        field_keys = {field.key for field in fields}
        expected_keys = {'exif_author', 'exif_datetime', 'gps_coords', 'exif_camera'}
        assert expected_keys.issubset(field_keys)

    def test_get_fields_for_document_type(self):
        """Тест получения полей для документов."""
        fields = MetadataRegistry.get_fields_for_file_type('document')
        
        # Проверяем, что возвращается список MetadataField
        assert isinstance(fields, list)
        assert all(isinstance(field, MetadataField) for field in fields)
        
        # Проверяем наличие основных полей для документов
        field_keys = {field.key for field in fields}
        expected_keys = {'author', 'created', 'modified', 'title', 'subject'}
        assert expected_keys.issubset(field_keys)

    def test_get_fields_for_pdf_type(self):
        """Тест получения полей для PDF."""
        fields = MetadataRegistry.get_fields_for_file_type('pdf')
        
        # Проверяем, что возвращается список MetadataField
        assert isinstance(fields, list)
        assert all(isinstance(field, MetadataField) for field in fields)
        
        # Проверяем наличие основных полей для PDF
        field_keys = {field.key for field in fields}
        expected_keys = {'author', 'creator', 'title', 'subject'}
        assert expected_keys.issubset(field_keys)

    def test_get_fields_for_video_type(self):
        """Тест получения полей для видео."""
        fields = MetadataRegistry.get_fields_for_file_type('video')
        
        # Проверяем, что возвращается список MetadataField
        assert isinstance(fields, list)
        assert all(isinstance(field, MetadataField) for field in fields)
        
        # Проверяем наличие основных полей для видео
        field_keys = {field.key for field in fields}
        expected_keys = {'author', 'creation_time', 'gps_coords', 'title'}
        assert expected_keys.issubset(field_keys)

    def test_get_fields_for_unsupported_type(self):
        """Тест получения полей для неподдерживаемого типа."""
        fields = MetadataRegistry.get_fields_for_file_type('unknown')
        
        # Для неподдерживаемого типа должен возвращаться пустой список
        assert fields == []

    def test_get_default_settings_for_file_type(self):
        """Тест получения настроек по умолчанию для типа файла."""
        settings = MetadataRegistry.get_default_settings_for_file_type('image')
        
        # Проверяем, что возвращается словарь
        assert isinstance(settings, dict)
        
        # Проверяем наличие ключевых настроек
        assert 'exif_author' in settings
        assert 'gps_coords' in settings
        
        # Проверяем, что настройки имеют правильный тип
        assert all(isinstance(value, bool) for value in settings.values())

    def test_get_field_by_key(self):
        """Тест поиска поля по ключу."""
        field = MetadataRegistry.get_field_by_key('image', 'exif_author')
        
        # Проверяем, что найдено поле
        assert field is not None
        assert isinstance(field, MetadataField)
        assert field.key == 'exif_author'
        assert field.category == MetadataCategory.AUTHOR

    def test_get_field_by_nonexistent_key(self):
        """Тест поиска несуществующего поля."""
        field = MetadataRegistry.get_field_by_key('image', 'nonexistent_key')
        
        # Для несуществующего ключа должен возвращаться None
        assert field is None

    def test_map_result_fields_to_metadata(self):
        """Тест сопоставления полей результата с метаданными."""
        result_fields = {
            'artist': 'Test Artist',
            'author': 'Test Author', 
            'gps_data': 'Test GPS',
            'unknown_field': 'Unknown'
        }
        
        mapping = MetadataRegistry.map_result_fields_to_metadata('image', result_fields)
        
        # Проверяем, что возвращается словарь
        assert isinstance(mapping, dict)
        
        # Проверяем, что известные поля сопоставлены
        assert 'exif_author' in mapping
        assert 'artist' in mapping['exif_author']
        
        assert 'gps_coords' in mapping
        assert 'gps_data' in mapping['gps_coords']

    def test_get_all_result_fields_for_file_type(self):
        """Тест получения всех возможных полей результата."""
        result_fields = MetadataRegistry.get_all_result_fields_for_file_type('image')
        
        # Проверяем, что возвращается множество
        assert isinstance(result_fields, set)
        
        # Проверяем наличие ожидаемых полей
        expected_fields = {'artist', 'author', 'gps_data', 'camera_make'}
        assert expected_fields.issubset(result_fields)

    def test_metadata_field_structure(self):
        """Тест структуры MetadataField."""
        fields = MetadataRegistry.get_fields_for_file_type('image')
        
        for field in fields:
            # Проверяем обязательные поля
            assert hasattr(field, 'key')
            assert hasattr(field, 'category')
            assert hasattr(field, 'name_key')
            assert hasattr(field, 'description_key')
            assert hasattr(field, 'result_fields')
            assert hasattr(field, 'default_remove')
            assert hasattr(field, 'priority')
            
            # Проверяем типы
            assert isinstance(field.key, str)
            assert isinstance(field.category, MetadataCategory)
            assert isinstance(field.result_fields, list)
            assert isinstance(field.default_remove, bool)
            assert isinstance(field.priority, int)

    def test_metadata_categories(self):
        """Тест категорий метаданных."""
        # Проверяем, что все категории определены
        categories = list(MetadataCategory)
        expected_categories = [
            MetadataCategory.AUTHOR,
            MetadataCategory.DATETIME,
            MetadataCategory.LOCATION,
            MetadataCategory.CAMERA,
            MetadataCategory.TECHNICAL,
            MetadataCategory.CONTENT
        ]
        
        for expected_cat in expected_categories:
            assert expected_cat in categories

    def test_default_remove_behavior(self):
        """Тест поведения настройки default_remove."""
        # Проверяем изображения
        image_fields = MetadataRegistry.get_fields_for_file_type('image')
        
        # Находим поле с default_remove=True
        author_fields = [f for f in image_fields if f.key == 'exif_author']
        assert len(author_fields) > 0
        assert author_fields[0].default_remove is True
        
        # Находим поле с default_remove=False
        copyright_fields = [f for f in image_fields if f.key == 'exif_copyright']
        if copyright_fields:  # Если такое поле существует
            assert copyright_fields[0].default_remove is False

    def test_priority_ordering(self):
        """Тест приоритетов полей."""
        fields = MetadataRegistry.get_fields_for_file_type('document')
        
        # Проверяем, что приоритеты заданы корректно
        for field in fields:
            assert isinstance(field.priority, int)
            assert field.priority >= 0
        
        # Проверяем, что авторские поля имеют высокий приоритет (низкие числа)
        author_fields = [f for f in fields if f.category == MetadataCategory.AUTHOR]
        if author_fields:
            for field in author_fields:
                assert field.priority <= 50  # Авторские поля должны иметь высокий приоритет