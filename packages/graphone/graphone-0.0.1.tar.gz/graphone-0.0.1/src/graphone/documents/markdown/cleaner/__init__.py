"""
Пакет для очистки Markdown документов.

Предоставляет гибкий API для очистки markdown текста с сохранением структуры.
Поддерживает настройку обработки различных элементов через Builder pattern.

Основное использование:
    >>> from agentone.documents.markdown.cleaner import MarkdownCleaner
    >>> 
    >>> # Простое использование
    >>> cleaner = MarkdownCleaner()
    >>> result = cleaner.clean(markdown_text)
    >>> 
    >>> # С настройкой через Builder
    >>> cleaner = (MarkdownCleaner.builder()
    ...     .images(strategy='preserve')
    ...     .links(strategy='clean')
    ...     .tables(strategy='clean')
    ...     .build())
    >>> result = cleaner.clean(markdown_text)
"""

from .markdown_cleaner import MarkdownCleaner
from .handlers import (
    ImageHandler,
    LinkHandler,
    TableHandler,
    CodeHandler,
)
from .strategies import ElementStrategy

__all__ = [
    'MarkdownCleaner',
    'ImageHandler',
    'LinkHandler',
    'TableHandler',
    'CodeHandler',
    'ElementStrategy',
]
