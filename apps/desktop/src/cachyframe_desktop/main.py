from __future__ import annotations

import asyncio

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from .window import MainWindow


def run() -> int:
    app = QApplication.instance() or QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        return loop.run_forever()

