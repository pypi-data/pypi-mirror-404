from textual.app import ComposeResult
from textual.widgets import Static, Button, Label
from textual.containers import Vertical
from textual.message import Message


class Sidebar(Static):
    """Левая панель навигации."""

    # Custom Message - для отправки событий родителю
    class Selected(Message):
        def __init__(self, item_id: str) -> None:
            self.item_id = item_id
            super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(classes="menu-container"):
            yield Label("AgentOne", classes="logo")
            yield Button("Конфигуратор", id="nav-configurator", classes="nav-btn")
            yield Static(classes="spacer")  # Отодвигает кнопку Выход вниз
            yield Button("Выход", id="nav-quit", variant="error", classes="nav-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Обработчик кликов на кнопки."""
        action = event.button.id.replace("nav-", "")  # "nav-configurator" -> "configurator"
        
        if action == "quit":
            self.app.exit()  # Выход из приложения
        else:
            self.post_message(self.Selected(action))  # Отправка сообщения вверх
