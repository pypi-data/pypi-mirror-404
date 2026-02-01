"""
Простой скрипт проверки очистки markdown документов.
"""
from pathlib import Path
from documents.markdown.cleaner import MarkdownCleaner
from documents.markdown.cleaner.strategies import ElementStrategy


def print_section(title: str, content: str, width: int = 80):
    """Выводит секцию с заголовком."""
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)
    print(content)
    print("=" * width + "\n")


def main():
    test_doc_path = Path(__file__).parent / "test_document.md"
    with open(test_doc_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    cleaner_main = (MarkdownCleaner.builder()
                    .images(strategy=ElementStrategy.REMOVE)  # Удаляем картинки
                    .links(strategy=ElementStrategy.REMOVE)  # Удаляем ссылки
                    .tables(strategy=ElementStrategy.CLEAN)  # Таблицы сохраняем, текст чистим
                    .code(strategy=ElementStrategy.REMOVE)  # Удаляем код
                    .build())
    cleaned_main = cleaner_main.clean(original_text)

    print(f"[OK] Очищено! Размер: {len(cleaned_main)} символов")
    print_section("РЕЗУЛЬТАТ ОСНОВНОЙ ОЧИСТКИ", cleaned_main)
    print("   Для сравнения: все элементы сохраняются")
    print("-" * 80)

    cleaner_default = MarkdownCleaner()
    cleaned_default = cleaner_default.clean(original_text)

    print(f"✅ Очищено! Размер: {len(cleaned_default)} символов")
    print_section("Результат базовой очистки", cleaned_default)
    print("\n" + "🔍 АНАЛИЗ ОСНОВНОГО РЕЖИМА")
    print("-" * 80)
    has_images = "![" in cleaned_main
    has_links = "](" in cleaned_main and "![" not in cleaned_main
    has_tables = "|" in cleaned_main
    has_code_blocks = "```" in cleaned_main
    has_inline_code = "`" in cleaned_main and "```" not in cleaned_main

    print(f"Картинки:       {'✅ Удалены' if not has_images else '❌ Остались'}")
    print(f"Ссылки:         {'✅ Удалены' if not has_links else '❌ Остались'}")
    print(f"Таблицы:        {'✅ Сохранены' if has_tables else '❌ Удалены'}")
    print(f"Блоки кода:     {'✅ Удалены' if not has_code_blocks else '❌ Остались'}")
    print(f"Инлайн код:     {'✅ Удален' if not has_inline_code else '❌ Остался'}")
    print("-" * 80)
    print("\n✨ Все тесты завершены!")


if __name__ == "__main__":
    main()
