"""
Обработчики различных элементов markdown (handlers).

Каждый handler отвечает за рендеринг конкретного типа элемента:
- ImageHandler: обработка изображений
- LinkHandler: обработка ссылок
- TableHandler: обработка таблиц
- CodeHandler: обработка блоков кода

Эти хендлеры предоставляют расширяемую архитектуру для кастомной обработки
различных типов markdown элементов.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from .strategies import ElementStrategy


class ElementHandler(ABC):
    """Базовый класс для обработчиков markdown элементов."""

    @abstractmethod
    def handle(self, token: Dict) -> Optional[Any]:
        """
        Обрабатывает токен AST и возвращает результат.
        Args:
            token: Токен AST из mistune парсера
        Returns:
            Обработанный токен, строка или None для удаления
        """
        pass


class ImageHandler(ElementHandler):
    """
    Обработчик изображений.

    Поддерживает стратегии:
    - preserve: сохранить изображение как есть
    - remove: удалить изображение
    - replace: заменить на placeholder
    """

    def __init__(self, strategy: ElementStrategy = ElementStrategy.PRESERVE, **options):
        self.strategy = strategy
        self.options = options

    def handle(self, token: Dict) -> Optional[Dict]:
        """Обрабатывает токен изображения."""
        if self.strategy == ElementStrategy.PRESERVE:
            return token
        elif self.strategy == ElementStrategy.REMOVE:
            return None
        elif self.strategy == ElementStrategy.REPLACE:
            # Заменяем URL и alt текст
            token['attrs']['url'] = self.options.get('placeholder_url', '')
            token['attrs']['alt'] = self.options.get('alt_text', 'Image')
            return token
        return token


class LinkHandler(ElementHandler):
    """
    Обработчик ссылок.

    Поддерживает стратегии:
    - preserve: сохранить ссылку как есть
    - remove: удалить URL, сохранить текст
    - extract_text: извлечь только текст без ссылки
    """

    def __init__(self, strategy: ElementStrategy = ElementStrategy.PRESERVE, **options):
        self.strategy = strategy
        self.options = options

    def handle(self, token: Dict) -> Optional[Any]:
        """Обрабатывает токен ссылки."""
        if self.strategy == ElementStrategy.PRESERVE:
            return token
        elif self.strategy == ElementStrategy.REMOVE or self.strategy == ElementStrategy.EXTRACT_TEXT:
            return token.get('children', [])
        return token


class TableHandler(ElementHandler):
    """
    Обработчик таблиц.
    Поддерживает стратегии:
    - preserve: сохранить таблицу как есть
    - clean: очистить текст в ячейках
    - remove: удалить таблицу
    """

    def __init__(self, strategy: ElementStrategy = ElementStrategy.CLEAN, **options):
        self.strategy = strategy
        self.options = options

    def handle(self, token: Dict) -> Optional[Dict]:
        """Обрабатывает токен таблицы."""
        if self.strategy == ElementStrategy.PRESERVE:
            return token
        elif self.strategy == ElementStrategy.CLEAN:
            return token
        elif self.strategy == ElementStrategy.REMOVE:
            return None
        return token


class CodeHandler(ElementHandler):
    """
    Обработчик кода (inline и block).

    Поддерживает стратегии:
    - preserve: сохранить код как есть (по умолчанию)
    - remove: удалить блоки кода
    """

    def __init__(self, strategy: ElementStrategy = ElementStrategy.PRESERVE, **options):
        self.strategy = strategy
        self.options = options

    def handle(self, token: Dict) -> Optional[Dict]:
        """Обрабатывает токен кода."""
        if self.strategy == ElementStrategy.PRESERVE:
            return token
        elif self.strategy == ElementStrategy.REMOVE:
            return None
        return token
