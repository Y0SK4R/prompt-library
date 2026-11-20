"""Run with ``python -m prompt_library``."""

import sys

from PySide6.QtWidgets import QApplication

from prompt_library.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Prompt Library")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
