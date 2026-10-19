"""Floating recorder widget: always on top, draggable, global hotkey."""
import time
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QObject, QSettings
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from botmeet.capture import Recorder, list_devices, write_wav
from botmeet.storage import session_dir

HOTKEY = "<ctrl>+<shift>+r"


class HotkeyBridge(QObject):
    pressed = Signal()


class FloatingWidget(QWidget):
    def __init__(self, root: Path):
        super().__init__()
        self._root = root
        self._recorder: Recorder | None = None
        self._started_at = 0.0
        self._hotkey_bridge = HotkeyBridge()
        self._hotkey_bridge.pressed.connect(self.toggle)

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        self._settings = QSettings("botmeet", "widget")

        self._project = QComboBox()
        self._project.setEditable(True)
        self._project.addItems(["demo"])
        self._project.setFixedWidth(110)
        self._project.setCurrentText(self._settings.value("project", "demo"))

        self._mic = QComboBox()
        try:
            mics = list_devices()["microphones"]
        except Exception:
            mics = []
        self._mic.addItems(mics)
        saved_mic = self._settings.value("mic", "")
        if saved_mic and saved_mic in mics:
            self._mic.setCurrentText(saved_mic)
        self._mic.setFixedWidth(150)
        self._mic.setToolTip("Microphone" )

        self._button = QPushButton("●")
        self._button.setFixedSize(36, 36)
        self._button.setStyleSheet(
            "QPushButton { background: #22c55e; color: white; border-radius: 18px; font-size: 16px; }"
        )
        self._button.clicked.connect(self.toggle)

        self._timer_label = QLabel("00:00")
        self._timer_label.setStyleSheet("color: white; font-size: 14px;")

        layout.addWidget(self._project)
        layout.addWidget(self._mic)
        layout.addWidget(self._button)
        layout.addWidget(self._timer_label)

        self.setStyleSheet("FloatingWidget { background: rgba(20, 20, 20, 220); border-radius: 12px; }")
        self.setFixedSize(410, 52)

        self._tick = QTimer(self)
        self._tick.setInterval(500)
        self._tick.timeout.connect(self._update_elapsed)

        self._drag_pos = None

    # -- dragging (frameless window) --
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # -- recording --
    def toggle(self):
        if self._recorder is None:
            self._settings.setValue("project", self._project.currentText())
            self._settings.setValue("mic", self._mic.currentText())
            self._recorder = Recorder(mic_id=self._mic.currentText() or None)
            self._recorder.start()
            self._started_at = time.monotonic()
            self._tick.start()
            self._button.setText("■")
            self._button.setStyleSheet(
                "QPushButton { background: #ef4444; color: white; border-radius: 18px; font-size: 14px; }"
            )
        else:
            stereo = self._recorder.stop()
            self._recorder = None
            self._tick.stop()
            session = session_dir(self._root, self._project.currentText().strip() or "demo", date.today())
            out = session / "audio.wav"
            write_wav(out, stereo)
            self._timer_label.setText("saved ✓")
            self._button.setText("●")
            self._button.setStyleSheet(
                "QPushButton { background: #22c55e; color: white; border-radius: 18px; font-size: 16px; }"
            )
            print(f"saved {out}", flush=True)

    def _update_elapsed(self):
        elapsed = int(time.monotonic() - self._started_at)
        self._timer_label.setText(f"{elapsed // 60:02d}:{elapsed % 60:02d}")

    def start_hotkey_listener(self):
        from pynput import keyboard

        def on_activate():
            self._hotkey_bridge.pressed.emit()

        listener = keyboard.GlobalHotKeys({HOTKEY: on_activate})
        listener.daemon = True
        listener.start()
        return listener


def run_widget(root: Path, smoke_seconds: float = 0.0) -> int:
    import os

    if os.name == "nt":
        import ctypes

        # Claim STA before Qt does: a prior MTA init (e.g. via audio/COM
        # imports) makes QWindowsContext.OleInitialize fail with 0x80010106.
        ctypes.windll.ole32.OleInitialize(None)
    app = QApplication([])
    widget = FloatingWidget(root)
    widget.start_hotkey_listener()
    widget.show()

    if smoke_seconds > 0:  # offscreen wiring check: record briefly, then quit
        QTimer.singleShot(500, widget.toggle)
        QTimer.singleShot(500 + int(smoke_seconds * 1000), widget.toggle)
        QTimer.singleShot(1000 + int(smoke_seconds * 1000), app.quit)

    return app.exec()
