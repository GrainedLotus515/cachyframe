from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FeatureTab(QWidget):
    def __init__(self, title: str, description: str, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        heading = QLabel(f"<h2>{title}</h2>")
        summary = QLabel(description)
        summary.setWordWrap(True)
        self.content = QPlainTextEdit()
        self.content.setReadOnly(True)
        layout.addWidget(heading)
        layout.addWidget(summary)
        layout.addWidget(self.content, stretch=1)

    def set_text(self, text: str) -> None:
        self.content.setPlainText(text)


class StatusPanel(QFrame):
    def __init__(self, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(self)
        self.backend_label = QLabel("Backend: unknown")
        self.collector_label = QLabel("Collectors: unknown")
        self.proxy_label = QLabel("Proxy: unknown")
        self.refresh_button = QPushButton("Refresh")
        layout.addWidget(self.backend_label)
        layout.addWidget(self.collector_label)
        layout.addWidget(self.proxy_label)
        layout.addStretch(1)
        layout.addWidget(self.refresh_button)

    def set_backend_status(self, text: str) -> None:
        self.backend_label.setText(f"Backend: {text}")

    def set_collector_status(self, text: str) -> None:
        self.collector_label.setText(f"Collectors: {text}")

    def set_proxy_status(self, text: str) -> None:
        self.proxy_label.setText(f"Proxy: {text}")


class OverlayWindow(QMainWindow):
    def __init__(self, title: str, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        body = QLabel(title)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setMargin(16)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(body)
        self.setCentralWidget(container)

