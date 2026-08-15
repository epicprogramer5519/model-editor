"""
MELCOR Model Editor — entry point.

Usage:
    python main.py [path/to/model.inp]
"""
import sys

from PySide6.QtWidgets import QApplication

from app.main_window import ModelEditorWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MELCOR Model Editor")

    filename = sys.argv[1] if len(sys.argv) > 1 else None
    window = ModelEditorWindow(filename)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
