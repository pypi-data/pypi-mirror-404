from __future__ import annotations
import sys

from PySide6.QtWidgets import QApplication

def main() -> None:
    # 触发示例算法注册
    import vibeflux.algorithms  # noqa: F401
    from vibeflux.gui import MainWindow

    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(980, 640)
    w.show()
    sys.exit(app.exec())
