from textual.app import ComposeResult
from textual.widgets import Static, Button, TabbedContent, TabPane, Checkbox
from textual.containers import VerticalScroll, Horizontal, Grid, Container
from textual.reactive import reactive
from agentone.tui.screens.modals import ConfigEditorModal


class Configurator(Static):
    """Экран конфигуратора приложения с вкладками."""
    
    # Reactive переменные
    notifications_enabled = reactive(True)
    email_notifications = reactive(True)
    sound_enabled = reactive(False)
    refresh_rate = reactive(5)
    auto_save = reactive(True)

    def on_mount(self) -> None:
        """Установка border_title после монтирования."""
        try:
            core_container = self.query_one("#core-container", Container)
            core_container.border_title = "⚙️ Ядро"
        except Exception:
            pass
        
        try:
            permissions_container = self.query_one("#permissions-container", Container)
            permissions_container.border_title = "✅ Разрешения"
        except Exception:
            pass
        
        try:
            features_container = self.query_one("#features-container", Container)
            features_container.border_title = "🚩 Фичефлаги"
        except Exception:
            pass
    
    def compose(self) -> ComposeResult:
        with TabbedContent():
            # Вкладка 1: Общие настройки
            with TabPane("🎛️ Общие", id="tab-general"):
                with VerticalScroll(classes="configurator-tab"):
                    # Секция: Ядро
                    with Container(classes="configurator-section core-section", id="core-container"):
                        with Grid(classes="core-buttons-grid"):
                            yield Button("⚙️ Конфигурация ядра", variant="success", id="btn-config", classes="core-button")
                            yield Button("🔄 Перезапустить", variant="error", id="btn-restart", classes="core-button")
            
            # Вкладка 2: Управление
            with TabPane("🎛️ Управление", id="tab-management"):
                with VerticalScroll(classes="configurator-tab"):
                    # Секция: Разрешения (заголовок устанавливается в on_mount)
                    with Container(classes="configurator-section permissions-section", id="permissions-container"):
                        with Grid(classes="permissions-grid"):
                            yield Checkbox("Разрешить удаленное управление", id="chk-remote", classes="permission-checkbox")
                            yield Checkbox("Разрешить экспорт данных", id="chk-export", value=True, classes="permission-checkbox")
                            yield Checkbox("Разрешить импорт конфигурации", id="chk-import", value=True, classes="permission-checkbox")
                            yield Checkbox("Включить двухфакторную аутентификацию", id="chk-2fa", classes="permission-checkbox")
                    
                    # Секция: Фичефлаги (заголовок устанавливается в on_mount)
                    with Container(classes="configurator-section permissions-section", id="features-container"):
                        with Grid(classes="permissions-grid"):
                            yield Checkbox("Включить экспериментальный UI", id="chk-feat-ui", classes="permission-checkbox")
                            yield Checkbox("Включить beta функции", id="chk-feat-beta", classes="permission-checkbox")
                            yield Checkbox("Включить отладочный режим", id="chk-feat-debug", classes="permission-checkbox")
                            yield Checkbox("Включить расширенную аналитику", id="chk-feat-analytics", classes="permission-checkbox")
                            yield Checkbox("Включить автообновления", id="chk-feat-autoupdate", value=True, classes="permission-checkbox")
                            yield Checkbox("Включить telemetry", id="chk-feat-telemetry", classes="permission-checkbox")
        
        # Кнопка сохранения внизу (вне вкладок)
        with Horizontal(classes="save-panel"):
            yield Button("💾 Сохранить все изменения", variant="success", id="btn-save", classes="save-button")

    def watch_notifications_enabled(self, new_val: bool) -> None:
        """Отслеживание изменения системных уведомлений."""
        if self.is_mounted:
            state = "включены" if new_val else "выключены"
            self.app.notify(f"Системные уведомления {state}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Обработка нажатия кнопок."""
        btn_id = event.button.id
        
        if btn_id == "btn-config":
            self._open_config_editor()
        elif btn_id == "btn-restart":
            self.app.notify("🔄 Перезапуск ядра...", severity="warning")
        elif btn_id == "btn-save":
            self.app.notify("✅ Все настройки сохранены", severity="information")
    
    def _open_config_editor(self) -> None:
        """Открыть редактор конфигурации."""
        config = """[core]
max_workers = 10
timeout = 30
log_level = INFO

[database]
host = localhost
port = 3306
user = agentone
password = secret

[redis]
host = localhost
port = 6379
db = 0

[api]
endpoint = https://api.sys-monitor.io/v1
rate_limit = 1000
"""
        
        def handle_result(result: tuple[str, bool] | None) -> None:
            if result:
                config_text, apply_to_redis = result
                self._save_config(config_text, apply_to_redis)
        
        self.app.push_screen(ConfigEditorModal(config), handle_result)
    
    def _save_config(self, config: str, apply_to_redis: bool) -> None:
        """Сохранить конфигурацию."""
        if apply_to_redis:
            self.app.notify("✅ Конфигурация сохранена в БД и применена в Redis", severity="information")
        else:
            self.app.notify("✅ Конфигурация сохранена в БД", severity="information")
