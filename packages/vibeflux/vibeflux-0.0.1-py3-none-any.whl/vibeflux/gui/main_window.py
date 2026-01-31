from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
)
from vibeflux.registry import list_components, get

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VibeFlux")

        root = QWidget()
        layout = QVBoxLayout(root)

        layout.addWidget(QLabel("VibeFlux — PySide6-based fusion toolkit for deep learning projects"))

        btn_row = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh Registry")
        self.btn_run_demo = QPushButton("Run Demo Algorithm")
        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_run_demo)
        layout.addLayout(btn_row)

        self.out = QTextEdit()
        self.out.setReadOnly(True)
        layout.addWidget(self.out)

        self.setCentralWidget(root)

        self.btn_refresh.clicked.connect(self.refresh_registry)
        self.btn_run_demo.clicked.connect(self.run_demo)

        self.refresh_registry()

    def log(self, s: str) -> None:
        self.out.append(s)

    def refresh_registry(self) -> None:
        comps = list_components()
        self.out.clear()
        self.log("Registered components:")
        for k, spec in comps.items():
            self.log(f"- {k} :: {spec.description}")

    def run_demo(self) -> None:
        spec = get(name="hello", kind="algorithm")
        algo = spec.factory()
        result = algo.run({"who": "PySide6 + DL"})
        self.log("")
        self.log("[Demo Result]")
        self.log(f"ok={result.ok}")
        self.log(f"metrics={result.metrics}")
        self.log(f"payload={result.payload}")
