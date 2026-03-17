import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFormLayout, QLineEdit,
    QSpinBox, QPushButton, QVBoxLayout, QLabel, QMessageBox
)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Create default config if missing
        default = {
            "main_window": {
                "url": "",
                "username": "",
                "password": ""
            },
            "overlay_window": {
                "url": "",
                "width": 610,
                "height": 600,
                "x": -10,
                "y": -100
            },
            "reload_interval_ms": 5000,
            "config_reload_interval_ms": 2000
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=4)
        return default

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


class Configurator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Overlay Configurator")
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # --- Main Window ---
        self.main_url = QLineEdit(self.config["main_window"].get("url", ""))
        self.main_user = QLineEdit(self.config["main_window"].get("username", ""))
        self.main_pass = QLineEdit(self.config["main_window"].get("password", ""))
        self.main_pass.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow(QLabel("<b>Main Window</b>"))
        layout.addRow("URL:", self.main_url)
        layout.addRow("Username:", self.main_user)
        layout.addRow("Password:", self.main_pass)

        # --- Overlay Window ---
        self.overlay_url = QLineEdit(self.config["overlay_window"].get("url", ""))
        self.overlay_width = QSpinBox()
        self.overlay_width.setRange(100, 2000)
        self.overlay_width.setValue(self.config["overlay_window"].get("width", 610))
        self.overlay_height = QSpinBox()
        self.overlay_height.setRange(100, 2000)
        self.overlay_height.setValue(self.config["overlay_window"].get("height", 600))
        self.overlay_x = QSpinBox()
        self.overlay_x.setRange(-2000, 2000)
        self.overlay_x.setValue(self.config["overlay_window"].get("x", -10))
        self.overlay_y = QSpinBox()
        self.overlay_y.setRange(-2000, 2000)
        self.overlay_y.setValue(self.config["overlay_window"].get("y", -100))

        layout.addRow(QLabel("<b>Overlay Window</b>"))
        layout.addRow("URL:", self.overlay_url)
        layout.addRow("Width:", self.overlay_width)
        layout.addRow("Height:", self.overlay_height)
        layout.addRow("X offset:", self.overlay_x)
        layout.addRow("Y offset:", self.overlay_y)

        # --- Reload intervals ---
        self.reload_interval = QSpinBox()
        self.reload_interval.setRange(1000, 60000)
        self.reload_interval.setValue(self.config.get("reload_interval_ms", 5000))
        self.config_reload_interval = QSpinBox()
        self.config_reload_interval.setRange(500, 10000)
        self.config_reload_interval.setValue(self.config.get("config_reload_interval_ms", 2000))
        layout.addRow(QLabel("<b>Intervals (ms)</b>"))
        layout.addRow("Reload interval:", self.reload_interval)
        layout.addRow("Config reload interval:", self.config_reload_interval)

        # --- Buttons ---
        self.save_btn = QPushButton("Save Config")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addRow(self.save_btn)

        self.setLayout(layout)

    def save_settings(self):
        self.config["main_window"]["url"] = self.main_url.text()
        self.config["main_window"]["username"] = self.main_user.text()
        self.config["main_window"]["password"] = self.main_pass.text()
        self.config["overlay_window"]["url"] = self.overlay_url.text()
        self.config["overlay_window"]["width"] = self.overlay_width.value()
        self.config["overlay_window"]["height"] = self.overlay_height.value()
        self.config["overlay_window"]["x"] = self.overlay_x.value()
        self.config["overlay_window"]["y"] = self.overlay_y.value()
        self.config["reload_interval_ms"] = self.reload_interval.value()
        self.config["config_reload_interval_ms"] = self.config_reload_interval.value()

        save_config(self.config)
        QMessageBox.information(self, "Saved", "Configuration saved successfully!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Configurator()
    window.show()
    sys.exit(app.exec())