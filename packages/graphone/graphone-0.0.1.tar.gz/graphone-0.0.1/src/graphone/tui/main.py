from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ContentSwitcher
from textual.containers import Container
from graphone.tui.widgets.sidebar import Sidebar
from graphone.tui.screens.configurator import Configurator
from graphone.tui.config import styles


class GraphOneControlPanel(App):
    """TUI приложение панели управления GraphOne."""
    
    ENABLE_COMMAND_PALETTE = False
    
    CSS = styles.get_style('app')
    
    BINDINGS = [
        ("q", "quit", "Выход"),
    ]
    
    TITLE = "GraphOne Control Panel"

    def compose(self) -> ComposeResult:
        """Построение DOM-дерева."""
        yield Header(show_clock=False)
        with Container(id="main-layout"):
            yield Sidebar(id="sidebar")
            with ContentSwitcher(initial="configurator"):
                yield Configurator(id="configurator")
        yield Footer()

    def on_mount(self) -> None:
        """Инициализация при старте."""
        self.theme = "tokyo-night"
        self.dark = True
        self.notify("Панель управления запущена!", severity="information")
    
    def watch_theme(self, theme: str) -> None:
        """Блокировка изменения темы."""
        if theme != "tokyo-night":
            self.theme = "tokyo-night"

    def on_sidebar_selected(self, message: Sidebar.Selected) -> None:
        """Обработка переключения экранов."""
        switcher = self.query_one(ContentSwitcher)
        switcher.current = message.item_id


def main():
    """Entry point для запуска TUI приложения."""
    app = GraphOneControlPanel()
    app.run()


if __name__ == "__main__":
    main()
