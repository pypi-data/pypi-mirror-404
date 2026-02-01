"""
Стратегии обработки элементов markdown.
"""
from enum import Enum


class ElementStrategy(Enum):
    """
    Стратегии обработки markdown элементов.
    
    Attributes:
        PRESERVE: Сохранить элемент как есть (с очисткой текста внутри)
        CLEAN: Очистить содержимое элемента
        REMOVE: Полностью удалить элемент
        REPLACE: Заменить элемент на другой
    """
    PRESERVE = "preserve"
    CLEAN = "clean"
    REMOVE = "remove"
    REPLACE = "replace"
    EXTRACT_TEXT = 'extract_text'
