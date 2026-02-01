from graphone.tui.config import styles
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, TextArea, RadioSet, RadioButton
from textual.containers import Vertical, Horizontal


class ConfigEditorModal(ModalScreen[tuple[str, bool] | None]):
    """Редактор INI конфигурации."""
    
    DEFAULT_CSS = styles.get_style('modals')

    def __init__(self, config_text: str):
        super().__init__()
        self.config_text = config_text

    def on_mount(self) -> None:
        """Установка дефолтного значения БД."""
        radio_buttons = self.query("RadioButton")
        if radio_buttons:
            radio_buttons[0].toggle()  # Выбрать первую кнопку (БД)

    def compose(self) -> ComposeResult:
        with Vertical(id="config-box"):
            yield Label("⚙️ Конфигурация ядра", classes="dialog-title")
            
            yield TextArea(
                self.config_text,
                show_line_numbers=True,
                id="config-textarea"
            )
            
            with Horizontal(classes="bottom-controls"):
                with RadioSet(id="redis-radio", classes="radio-left"):
                    yield RadioButton("📀 БД", value=False)
                    yield RadioButton("⚡ Redis", value=False)
                with Horizontal(classes="button-container"):
                    yield Button("Отмена", variant="default", id="btn-cancel", classes="btn-right")
                    yield Button("Сохранить", variant="primary", id="btn-save", classes="btn-right")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            textarea = self.query_one("#config-textarea", TextArea)
            radio_set = self.query_one("#redis-radio", RadioSet)
            apply_to_redis = radio_set.pressed_index == 1
            self.dismiss((textarea.text, apply_to_redis))
        else:
            self.dismiss(None)
