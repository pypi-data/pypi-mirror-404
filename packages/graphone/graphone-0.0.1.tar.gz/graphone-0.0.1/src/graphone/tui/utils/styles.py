from pathlib import Path


class Styles:
    """
    Утилиты для управления стилями AgentOne TUI
    """

    def __init__(self, styles_directory: Path):
        self.styles_directory: Path = styles_directory

    def get_style(self, name: str, ext: str = 'tcss') -> str:
        """
        Возвращает содержимое файла со стилями в виде строки для передачи в textual формате.
        :param name: Имя файла со стилями.
        :param ext: Расширение файла со стилями (опционально).
        :return: Возвращает строку с содержимым файла стилей.
        """
        file_path = self.styles_directory / f"{name}.{ext}"
        if not file_path.exists():
            raise FileNotFoundError(f"Style file not found: {file_path}")
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
