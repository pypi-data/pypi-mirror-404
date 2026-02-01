"""
Основной класс для очистки markdown документов.

MarkdownCleaner использует AST парсинг для разделения структуры 
и текстового содержимого, применяя очистку только к тексту.
"""
from __future__ import annotations
from typing import Optional, Any, List, Union
from mistune import create_markdown
from re import sub

from .config import CleaningRules
from .strategies import ElementStrategy


class MarkdownCleanerBuilder:
    """
    Builder для настройки MarkdownCleaner.

    Предоставляет fluent API для конфигурации обработки различных элементов.
    """

    def __init__(self):
        self._text_rules = CleaningRules()
        self._image_strategy, self._image_options = ElementStrategy.PRESERVE, {}
        self._link_strategy, self._link_options = ElementStrategy.PRESERVE, {}
        self._table_strategy, self._table_options = ElementStrategy.CLEAN, {}
        self._code_strategy, self._code_options = ElementStrategy.PRESERVE, {}

    def text(self, rules: CleaningRules) -> MarkdownCleanerBuilder:
        """Настройка правил очистки текста."""
        self._text_rules = rules
        return self

    def images(self, strategy: ElementStrategy = ElementStrategy.PRESERVE, **options) -> MarkdownCleanerBuilder:
        """Настройка обработки изображений."""
        self._image_strategy = strategy
        self._image_options = options
        return self

    def links(self, strategy: ElementStrategy = ElementStrategy.PRESERVE, **options) -> MarkdownCleanerBuilder:
        """Настройка обработки ссылок."""
        self._link_strategy = strategy
        self._link_options = options
        return self

    def tables(self, strategy: ElementStrategy = ElementStrategy.CLEAN, **options) -> MarkdownCleanerBuilder:
        """Настройка обработки таблиц."""
        self._table_strategy = strategy
        self._table_options = options
        return self

    def code(self, strategy: ElementStrategy = ElementStrategy.PRESERVE, **options) -> MarkdownCleanerBuilder:
        """Настройка обработки кода."""
        self._code_strategy = strategy
        self._code_options = options
        return self

    def build(self) -> MarkdownCleaner:
        """Создает настроенный экземпляр MarkdownCleaner."""
        return MarkdownCleaner(
            text_rules=self._text_rules,
            image_strategy=self._image_strategy,
            image_options=self._image_options,
            link_strategy=self._link_strategy,
            link_options=self._link_options,
            table_strategy=self._table_strategy,
            table_options=self._table_options,
            code_strategy=self._code_strategy,
            code_options=self._code_options
        )


class MarkdownCleaner:
    """
    Очиститель markdown документов с поддержкой гибкой настройки.
    Использует AST парсинг (mistune) для разделения разметки и текста.
    Очистка применяется только к текстовым нодам, остальная структура сохраняется.
    Examples:
        Простое использование:
        >>> cleaner = MarkdownCleaner()
        >>> result = cleaner.clean(markdown_text)

        С настройкой:
        >>> cleaner = (MarkdownCleaner.builder()
        ...     .images(strategy=ElementStrategy.PRESERVE)
        ...     .links(strategy=ElementStrategy.CLEAN)
        ...     .build())
        >>> result = cleaner.clean(markdown_text)
    """

    def __init__(
            self,
            text_rules: CleaningRules = None,
            image_strategy: ElementStrategy = ElementStrategy.PRESERVE,
            image_options: dict = None,
            link_strategy: ElementStrategy = ElementStrategy.PRESERVE,
            link_options: dict = None,
            table_strategy: ElementStrategy = ElementStrategy.CLEAN,
            table_options: dict = None,
            code_strategy: ElementStrategy = ElementStrategy.PRESERVE,
            code_options: dict = None
    ):
        self.text_rules = text_rules or CleaningRules()
        self.image_strategy = image_strategy
        self.image_options = image_options or {}
        self.link_strategy = link_strategy
        self.link_options = link_options or {}
        self.table_strategy = table_strategy
        self.table_options = table_options or {}
        self.code_strategy = code_strategy
        self.code_options = code_options or {}

        self.markdown = create_markdown(renderer='ast', plugins=['table', 'strikethrough'])

    @classmethod
    def builder(cls) -> MarkdownCleanerBuilder:
        """Создает Builder для настройки cleaner."""
        return MarkdownCleanerBuilder()

    def clean(self, markdown_text: str) -> str:
        """
        Очищает markdown текст.
        Args:
            markdown_text: Исходный markdown текст
        Returns:
            Очищенный markdown текст с сохраненной структурой
        """
        if not markdown_text or not markdown_text.strip():
            return markdown_text

        ast = self.markdown(markdown_text)  # markdown в AST
        cleaned_ast = self._process_node(ast)  # обработка AST рекурсивно
        return self._render_ast(cleaned_ast)  # AST в markdown

    def _process_node(self, node: Any) -> Any:
        """Рекурсивно обрабатывает ноды AST."""
        if isinstance(node, list):
            return [self._process_node(item) for item in node if item is not None]
        if not isinstance(node, dict):
            return node

        node_type = node.get('type')
        # правила очистки только к текстовым нодам
        if node_type == 'text':
            if node.get('raw'):
                node['raw'] = self._clean_text(node.get('raw'))
            return node
        # другие типы нод согласно стратегиям
        if node_type == 'image':
            return self._process_image(node)
        elif node_type == 'link':
            return self._process_link(node)
        elif node_type == 'code_block' or node_type == 'codespan':
            return self._process_code(node)
        elif node_type == 'table':
            return self._process_table(node)
        # дочерние элементы
        if 'children' in node:
            node['children'] = self._process_node(node['children'])

        return node

    def _clean_text(self, text: str) -> str:
        """
        Очищает текст согласно правилам CleaningRules.
        Применяет белый список символов - удаляет все символы,
        которые не являются буквами/цифрами и не входят в белый список.
        """
        if not text:  # если вдруг в узле пустая строка, строго гворя параметр есть, но чистить его смысла нет
            return text

        result = []
        for char in text:
            if self.text_rules.should_replace_with_space(char):
                result.append(' ')
            elif self.text_rules.is_allowed(char):
                result.append(char)
            # иначе символ удаляется

        cleaned = ''.join(result)

        if self.text_rules.NORMALIZE_SPACES:  # Нормализация пробелов если включена
            cleaned = sub(r'[ \t]+', ' ', cleaned)  # Заменяем множественные пробелы и табы на один пробел

        return cleaned

    def _process_image(self, node: dict) -> Optional[dict]:
        """Обрабатывает изображение согласно стратегии."""
        if self.image_strategy == ElementStrategy.PRESERVE:
            return node
        elif self.image_strategy == ElementStrategy.REMOVE:
            return None
        elif self.image_strategy == ElementStrategy.REPLACE:
            node['attrs']['url'] = self.image_options.get('placeholder_url', '')
            node['attrs']['title'] = self.image_options.get('alt_text', 'Image')
            return node
        return node

    def _process_link(self, node: dict) -> Union[dict, List, None]:
        """Обрабатывает ссылку согласно стратегии."""
        if self.link_strategy == ElementStrategy.PRESERVE:
            if 'children' in node:
                node['children'] = self._process_node(node['children'])
            return node
        elif self.link_strategy == ElementStrategy.REMOVE:
            # удаляем ссылку, но сохраняем текст внутри
            if 'children' in node:
                return self._process_node(node['children'])
            return {'type': 'text', 'raw': ''}
        return node

    def _process_code(self, node: dict) -> Optional[dict]:
        """Обрабатывает код согласно стратегии."""
        if self.code_strategy == ElementStrategy.PRESERVE:
            return node
        elif self.code_strategy == ElementStrategy.REMOVE:
            return None
        return node

    def _process_table(self, node: dict) -> Optional[dict]:
        """Обрабатывает таблицу согласно стратегии."""
        if self.table_strategy == ElementStrategy.PRESERVE:
            return node
        elif self.table_strategy == ElementStrategy.CLEAN:  # чистить текст в ячейках таблицы
            if 'children' in node:
                node['children'] = self._process_node(node['children'])
            return node
        elif self.table_strategy == ElementStrategy.REMOVE:
            return None
        return node

    def _render_ast(self, ast: Any) -> str:
        """Рендерит AST обратно в markdown."""
        if isinstance(ast, list):
            return ''.join(self._render_node(node) for node in ast if node is not None)
        return self._render_node(ast)

    def _render_node(self, node: Any) -> str:
        """Рендерит отдельную ноду в markdown."""
        if node is None:
            return ''
        if isinstance(node, str):
            return node
        if isinstance(node, list):
            return ''.join(self._render_node(n) for n in node if n is not None)
        if not isinstance(node, dict):
            return str(node)

        node_type = node.get('type')
        match node_type:
            case 'text':
                return node.get('raw', '')
            case 'paragraph':
                content = self._render_children(node)
                return f"{content}\n\n"
            case 'heading':
                level = node.get('attrs', {}).get('level', 1)
                content = self._render_children(node)
                return f"{'#' * level} {content}\n\n"
            case 'list':
                items = self._render_children(node)
                return f"{items}\n"
            case 'list_item':
                content = self._render_children(node)
                ordered = node.get('attrs', {}).get('ordered', False)
                prefix = '1. ' if ordered else '- '
                return f"{prefix}{content}\n"
            case 'link':
                url = node.get('attrs', {}).get('url', '')
                title = node.get('attrs', {}).get('title', '')
                content = self._render_children(node)
                if title:
                    return f"[{content}]({url} \"{title}\")"
                return f"[{content}]({url})"
            case 'image':
                url = node.get('attrs', {}).get('url', '')
                alt = node.get('attrs', {}).get('alt', '')
                title = node.get('attrs', {}).get('title', '')
                if title:
                    return f"![{alt}]({url} \"{title}\")"
                return f"![{alt}]({url})"
            case 'code_block':
                lang = node.get('attrs', {}).get('info', '')
                code = node.get('raw', '')
                return f"```{lang}\n{code}\n```\n\n"
            case 'codespan':
                return f"`{node.get('raw', '')}`"
            case 'block_quote':
                content = self._render_children(node)
                lines = content.split('\n')
                quoted = '\n'.join(f"> {line}" for line in lines if line)
                return f"{quoted}\n\n"
            case 'table':
                return self._render_table(node)
            case 'strong':
                content = self._render_children(node)
                return f"**{content}**"
            case 'emphasis':
                content = self._render_children(node)
                return f"*{content}*"
            case 'strikethrough':
                content = self._render_children(node)
                return f"~~{content}~~"
            case 'thematic_break':
                return "---\n\n"
            case 'linebreak':
                return "\n"
            case 'softbreak':
                return " "
            case 'document':
                return self._render_children(node)

        # По умолчанию рендерим дочерние элементы
        return self._render_children(node)

    def _render_children(self, node: dict) -> str:
        """Рендерит дочерние элементы ноды."""
        children = node.get('children', [])
        if isinstance(children, list):
            return ''.join(self._render_node(child) for child in children if child is not None)
        return ''

    def _render_table(self, node: dict) -> str:
        """Рендерит таблицу."""
        children = node.get('children', [])
        if not children:
            return ''
        rows = []
        header_row = None
        for child in children:
            if child.get('type') == 'table_head':
                header_row = self._render_table_row(child, is_header=True)
            elif child.get('type') == 'table_body':
                for row_node in child.get('children', []):
                    if row_node:
                        rendered = self._render_table_row(row_node)
                        if rendered:
                            rows.append(rendered[0])
        result = []
        if header_row:
            result.append(header_row[0])
            result.append(header_row[1])
        result.extend(rows)

        return '\n'.join(result) + '\n\n'

    def _render_table_row(self, row_node: dict, is_header: bool = False) -> tuple | None:
        """Рендерит строку таблицы."""
        cells = []
        for cell_node in row_node.get('children', []):
            if cell_node:
                content = self._render_children(cell_node).strip()
                cells.append(content)
        if not cells:
            return None
        row = '| ' + ' | '.join(cells) + ' |'
        if is_header:
            separator = '| ' + ' | '.join(['---'] * len(cells)) + ' |'
            return row, separator

        return (row,)
