"""
window.py — Main application window.

Layout:
  ┌──────────────────────────────────────────────┐
  │  TOOLBAR: logo · title · [Open] [Export]     │
  ├──────────────────────────────────────────────┤
  │  DROP ZONE  (shown when no PDF loaded)       │
  │   ──or──                                     │
  │  TEXT BROWSER  (shown after PDF loaded)      │
  ├──────────────────────────────────────────────┤
  │  STATUS BAR: page count · word count         │
  └──────────────────────────────────────────────┘

Design: Dark Atelier Typographer
  Chrome:  #0a0806 bg · #d4942a amber accent · #e8e2d8 warm ivory text
  Reading: #f6f0e6 warm paper · #1a0e00 bold anchors
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QSize, QTimer
from PyQt6.QtGui import (
    QColor, QDragEnterEvent, QDropEvent, QIcon, QFont,
    QPainter, QPen, QBrush, QPalette, QFontDatabase,
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton,
    QSizePolicy, QStackedWidget, QStatusBar, QTextBrowser,
    QVBoxLayout, QWidget, QProgressBar,
)

from extractor import extract_pdf, word_count
from renderer import render_html, render_empty_html


# ── Colour tokens ────────────────────────────────────────────────────────────
C_BG         = "#0a0806"
C_SURFACE    = "#12100e"
C_TOOLBAR    = "#0f0d0b"
C_SEPARATOR  = "#231f1b"
C_ACCENT     = "#d4942a"
C_ACCENT_DIM = "#7a500f"
C_TEXT       = "#e8e2d8"
C_TEXT_DIM   = "#6e6259"
C_PAPER      = "#f6f0e6"
C_PAPER_DARK = "#e8dfd0"

# ── Stylesheet ───────────────────────────────────────────────────────────────
APP_QSS = f"""
/* ── Window / central widget ──────────────────────────────────────────── */
QMainWindow {{
    background-color: {C_BG};
}}
QWidget#central {{
    background-color: {C_BG};
}}

/* ── Toolbar ──────────────────────────────────────────────────────────── */
QWidget#toolbar {{
    background-color: {C_TOOLBAR};
    border-bottom: 1px solid {C_SEPARATOR};
    min-height: 52px;
    max-height: 52px;
}}

/* ── Logo / title labels ──────────────────────────────────────────────── */
QLabel#logo {{
    font-family: "Courier New";
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 3px;
    color: {C_ACCENT};
    padding-left: 20px;
}}
QLabel#doc-title {{
    font-family: "Courier New";
    font-size: 11px;
    letter-spacing: 1px;
    color: {C_TEXT_DIM};
    padding: 0 12px;
}}

/* ── Buttons ──────────────────────────────────────────────────────────── */
QPushButton {{
    font-family: "Courier New";
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1.5px;
    color: {C_ACCENT};
    background-color: transparent;
    border: 1px solid {C_ACCENT_DIM};
    border-radius: 3px;
    padding: 6px 16px;
    min-width: 72px;
}}
QPushButton:hover {{
    background-color: {C_ACCENT};
    color: {C_BG};
    border-color: {C_ACCENT};
}}
QPushButton:pressed {{
    background-color: {C_ACCENT_DIM};
    border-color: {C_ACCENT_DIM};
}}
QPushButton:disabled {{
    color: {C_TEXT_DIM};
    border-color: {C_SEPARATOR};
}}

/* ── Drop zone ────────────────────────────────────────────────────────── */
QFrame#drop-zone {{
    background-color: {C_BG};
    border: 2px dashed {C_ACCENT_DIM};
    border-radius: 12px;
    margin: 40px;
}}
QFrame#drop-zone:hover {{
    border-color: {C_ACCENT};
}}
QLabel#drop-icon {{
    font-size: 48px;
    color: {C_ACCENT_DIM};
}}
QLabel#drop-heading {{
    font-family: "Courier New";
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 2px;
    color: {C_TEXT_DIM};
}}
QLabel#drop-subtext {{
    font-family: "Courier New";
    font-size: 10px;
    letter-spacing: 1px;
    color: {C_TEXT_DIM};
    padding-top: 6px;
}}

/* ── Text browser (reading canvas) ───────────────────────────────────── */
QTextBrowser {{
    background-color: {C_PAPER};
    border: none;
    margin: 0;
    padding: 0;
    selection-background-color: {C_ACCENT};
    selection-color: {C_BG};
    font-family: Lora, Georgia, serif;
    font-size: 17px;
    line-height: 1.85;
}}
/* Scrollbar ─────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {C_SURFACE};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C_ACCENT_DIM};
    border-radius: 4px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C_ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ── Status bar ──────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {C_TOOLBAR};
    border-top: 1px solid {C_SEPARATOR};
    font-family: "Courier New";
    font-size: 10px;
    letter-spacing: 1px;
    color: {C_TEXT_DIM};
    min-height: 28px;
}}
QStatusBar QLabel {{
    color: {C_TEXT_DIM};
    padding: 0 12px;
}}

/* ── Progress widget ─────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {C_SEPARATOR};
    border: none;
    border-radius: 2px;
    height: 3px;
    max-height: 3px;
}}
QProgressBar::chunk {{
    background-color: {C_ACCENT};
    border-radius: 2px;
}}
"""


# ── Worker thread for PDF loading ────────────────────────────────────────────
class PdfWorker(QObject):
    """Runs PDF extraction + HTML render off the main thread."""
    finished = pyqtSignal(list, str)   # pages, html
    error    = pyqtSignal(str)

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def run(self) -> None:
        try:
            pages = extract_pdf(self._path)
            title = Path(self._path).stem
            html  = render_html(pages, title=title)
            self.finished.emit(pages, html)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


# ── Drop zone widget ─────────────────────────────────────────────────────────
class DropZone(QFrame):
    """Animated dashed-border drop target shown when no PDF is loaded."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("drop-zone")
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon = QLabel("⬡")
        icon.setObjectName("drop-icon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        heading = QLabel("DROP A PDF HERE")
        heading.setObjectName("drop-heading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtext = QLabel("or click  OPEN  above")
        subtext.setObjectName("drop-subtext")
        subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon)
        layout.addWidget(heading)
        layout.addWidget(subtext)


# ── Main window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._pages:    list[dict] = []
        self._html:     str        = ""
        self._filepath: str        = ""
        self._worker_thread: QThread | None = None

        self.setWindowTitle("Bionic Reader")
        self.setMinimumSize(760, 560)
        self.resize(920, 700)
        self.setAcceptDrops(True)

        self._build_ui()
        self._apply_styles()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_progress_bar())
        root.addWidget(self._build_stack(), stretch=1)

        self._build_status_bar()

    def _build_toolbar(self) -> QWidget:
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        row = QHBoxLayout(toolbar)
        row.setContentsMargins(0, 0, 16, 0)
        row.setSpacing(0)

        self._lbl_logo = QLabel("◈  BIONIC")
        self._lbl_logo.setObjectName("logo")

        self._lbl_title = QLabel("no document")
        self._lbl_title.setObjectName("doc-title")
        self._lbl_title.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        self._btn_open   = QPushButton("OPEN")
        self._btn_export = QPushButton("EXPORT")
        self._btn_export.setEnabled(False)

        self._btn_open.clicked.connect(self._on_open)
        self._btn_export.clicked.connect(self._on_export)

        row.addWidget(self._lbl_logo)
        row.addSpacing(24)
        row.addWidget(self._lbl_title)
        row.addSpacing(12)
        row.addWidget(self._btn_open)
        row.addSpacing(8)
        row.addWidget(self._btn_export)

        return toolbar

    def _build_progress_bar(self) -> QProgressBar:
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)          # indeterminate mode
        self._progress.setMaximumHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        return self._progress

    def _build_stack(self) -> QStackedWidget:
        self._stack = QStackedWidget()

        # Index 0 — drop zone
        self._drop_zone = DropZone()
        self._stack.addWidget(self._drop_zone)

        # Index 1 — reading canvas
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setReadOnly(True)
        self._browser.document().setDefaultStyleSheet(self._reading_css())
        self._stack.addWidget(self._browser)

        return self._stack

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_lbl = QLabel("ready")
        sb.addWidget(self._status_lbl)

    # ── Styles ────────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        self.setStyleSheet(APP_QSS)

    @staticmethod
    def _reading_css() -> str:
        """CSS injected into QTextBrowser's document."""
        return f"""
        body {{
            font-family: Lora, Georgia, "Times New Roman", serif;
            font-size: 17px;
            line-height: 1.85;
            color: #2a2420;
            background-color: {C_PAPER};
            margin: 0;
            padding: 0;
        }}
        .page-marker {{
            font-family: "Courier New", Courier, monospace;
            font-size: 10px;
            letter-spacing: 4px;
            color: #b8a890;
            border-bottom: 1px solid #d8cfc0;
            margin-top: 36px;
            margin-bottom: 24px;
            padding-bottom: 6px;
        }}
        p {{
            margin: 0 0 16px 0;
            padding: 0;
        }}
        h2 {{
            font-size: 20px;
            font-weight: bold;
            color: #1a0e00;
            margin: 28px 0 10px;
            padding: 0;
        }}
        b, strong {{
            font-weight: bold;
            color: #1a0e00;
        }}
        """

    # ── Drag-and-drop ─────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".pdf") for u in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                self._load_pdf(path)
                break

    # ── PDF loading ───────────────────────────────────────────────────────

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF",
            str(Path.home()),
            "PDF files (*.pdf);;All files (*)",
        )
        if path:
            self._load_pdf(path)

    def _load_pdf(self, path: str) -> None:
        self._filepath = path
        name = Path(path).name
        self._lbl_title.setText(name)
        self._status_lbl.setText(f"processing  {name} …")
        self._btn_open.setEnabled(False)
        self._btn_export.setEnabled(False)
        self._progress.setVisible(True)

        # Run extraction in a background thread to keep UI live
        self._thread = QThread()
        self._worker = PdfWorker(path)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_load_finished)
        self._worker.error.connect(self._on_load_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_load_finished(self, pages: list[dict], html: str) -> None:
        self._pages = pages
        self._html  = html

        total_pages = len(pages)
        total_words = word_count(pages)

        # Wrap content with padding for the browser
        padded_html = html.replace(
            "<body>",
            "<body style='padding: 48px 48px 80px; max-width: 680px; margin: 0 auto;'>",
        )
        self._browser.setHtml(padded_html)
        self._stack.setCurrentIndex(1)

        self._status_lbl.setText(
            f"◈  {total_pages} page{'s' if total_pages != 1 else ''}  ·  "
            f"{total_words:,} words"
        )
        self._progress.setVisible(False)
        self._btn_open.setEnabled(True)
        self._btn_export.setEnabled(True)

    def _on_load_error(self, msg: str) -> None:
        self._progress.setVisible(False)
        self._btn_open.setEnabled(True)
        self._lbl_title.setText("error loading file")
        self._status_lbl.setText("error")
        QMessageBox.critical(self, "Load Error", f"Could not read PDF:\n\n{msg}")

    # ── Export ─────────────────────────────────────────────────────────────

    def _on_export(self) -> None:
        if not self._html:
            return

        stem = Path(self._filepath).stem if self._filepath else "bionic"
        default = str(Path.home() / f"{stem}_bionic.html")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Bionic HTML",
            default,
            "HTML files (*.html);;All files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._html)
            self._status_lbl.setText(f"exported → {Path(path).name}")
        except OSError as exc:
            QMessageBox.critical(self, "Export Error", f"Could not save:\n\n{exc}")
