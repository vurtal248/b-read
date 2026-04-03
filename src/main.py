"""
main.py — Entry point for Bionic Reader.

Run in dev:     python src/main.py
Run as .exe:    BionicReader.exe  (after PyInstaller build)
"""

import sys
import os

# When running from a PyInstaller --onefile bundle, sys._MEIPASS is set and
# the extracted modules live there. Prepend it so relative imports work.
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS  # type: ignore[attr-defined]
    if _base not in sys.path:
        sys.path.insert(0, _base)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from window import MainWindow


def main() -> None:
    # High-DPI on Windows 10/11
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Bionic Reader")
    app.setApplicationVersion("1.0.0")

    # Open PDF passed as CLI argument (e.g. double-click .pdf in Explorer)
    window = MainWindow()
    window.show()

    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if candidate.lower().endswith(".pdf") and os.path.isfile(candidate):
            window._load_pdf(candidate)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
