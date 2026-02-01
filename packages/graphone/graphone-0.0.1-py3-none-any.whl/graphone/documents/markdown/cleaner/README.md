# Cleaner Package

Пакет для гибкой очистки Markdown документов с сохранением структуры.

## 🎯 Особенности

- **AST-based парсинг** - разделение разметки и текстового содержимого
- **Гибкая настройка** - управление обработкой каждого типа элементов
- **Builder pattern** - удобный fluent API
- **Расширяемость** - легко добавить кастомные обработчики

## 📦 Структура пакета

```
cleaner/
├── __init__.py              # Публичный API
├── markdown_cleaner.py      # Основной класс и Builder
├── handlers.py              # Обработчики элементов (Image, Link, Table, Code)
└── strategies.py            # Стратегии обработки (Preserve, Clean, Remove, Replace)
```

## 🚀 Использование

### Простое использование (defaults)

```python
from modules.document_processor.services.cleaner import MarkdownCleaner

cleaner = MarkdownCleaner()
result = cleaner.clean(markdown_text)
```

### С настройкой через Builder

```python
cleaner = (MarkdownCleaner.builder()
    .images(strategy='preserve')
    .links(strategy='clean')
    .tables(strategy='clean')
    .code(strategy='preserve')
    .build())

result = cleaner.clean(markdown_text)
```

## 🎨 Стратегии обработки

- **preserve** - сохранить элемент как есть (с очисткой текста)
- **clean** - очистить содержимое
- **remove** - удалить элемент полностью
- **replace** - заменить на другой элемент

## 🔧 API элементов

### Текст
```python
.text(rules=CleaningRules())
```

### Изображения
```python
.images(strategy='preserve')
.images(strategy='replace', placeholder_url='https://...', alt_text='Image')
.images(strategy='remove')
```

### Ссылки
```python
.links(strategy='preserve')
.links(strategy='remove')  # Удаляет URL, но оставляет текст
```

### Таблицы
```python
.tables(strategy='clean')    # Очистка текста в ячейках
.tables(strategy='preserve')  # Без изменений
.tables(strategy='remove')    # Удалить таблицы
```

### Код
```python
.code(strategy='preserve')  # Не трогать код
.code(strategy='remove')    # Удалить блоки кода
```

## 📝 Примеры

### Замена всех изображений на placeholder

```python
cleaner = (MarkdownCleaner.builder()
    .images(
        strategy='replace',
        placeholder_url='https://via.placeholder.com/150',
        alt_text='Removed Image'
    )
    .build())
```

### Удаление ссылок, сохранение текста

```python
cleaner = (MarkdownCleaner.builder()
    .links(strategy='remove')
    .build())
```

### Кастомные правила очистки текста

```python
from modules.document_processor.config import CleaningRules

custom_rules = CleaningRules()
custom_rules.ALLOWED_CHARS = set(' .,!?-абвгдежзийклмнопрстуфхцчшщъыьэюя')

cleaner = (MarkdownCleaner.builder()
    .text(rules=custom_rules)
    .build())
```

## 🔍 Что очищается

### Текстовое содержимое
- Спецсимволы (согласно CleaningRules)
- Множественные пробелы
- Символы замены (например, `/` → пробел)

### Что НЕ очищается (по умолчанию)
- Markdown разметка (заголовки, списки, и т.д.)
- URL в ссылках и изображениях
- Содержимое блоков кода
- Структура таблиц
