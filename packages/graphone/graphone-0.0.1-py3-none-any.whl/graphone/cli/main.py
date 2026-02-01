"""Главный CLI интерфейс GraphOne."""
from sys import argv, exit


def show_help():
    """Показать справку по командам."""
    print("""
GraphOne - Node management and control system

Usage:
    graphone do         Запустить CLI операции
    graphone control    Запустить TUI панель управления
    graphone --help     Показать эту справку
    graphone --version  Показать версию

Examples:
    graphone do         # Запуск CLI режима
    graphone control    # Запуск TUI панели управления
""")


def show_version():
    """Показать версию."""
    print("GraphOne v0.0.1")


def do_command():
    """CLI режим - операции и команды."""
    print("GraphOne CLI Mode")
    print("Node management system ready!")
    # Здесь будет логика CLI команд для управления узлом


def control_command():
    """TUI режим - панель управления."""
    try:
        from graphone.tui.main import main as tui_main
        tui_main()
    except ImportError:
        print("ERROR: TUI not available. Install with: pip install graphone[tui]")
        exit(1)


def main():
    """Главная точка входа CLI."""
    # TODO Переделать на ArgsParser когда дойдет до реализации.
    args = argv[1:]
    
    if not args or args[0] in ['--help', '-h', 'help']:
        show_help()
        return
    
    if args[0] in ['--version', '-v', 'version']:
        show_version()
        return
    
    command = args[0]
    
    if command == 'do':
        do_command()
    elif command == 'control':
        control_command()
    else:
        print(f"ERROR: Unknown command: {command}")
        print("Use 'graphone --help' for help")
        exit(1)


if __name__ == "__main__":
    main()
