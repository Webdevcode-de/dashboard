import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QLineEdit, QSpinBox, QPushButton, QLabel, QMessageBox, QFileDialog

CONFIG_FOLDER = os.path.join(os.path.expanduser("~"), ".screenapp")
CONFIG_FILE = os.path.join(CONFIG_FOLDER, "config.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(CONFIG_FOLDER, exist_ok=True)
        default = {
            "main_window": {"url": "", "username": "", "password": ""},
            "overlay_window": {"url": "", "width": 610, "height": 600, "x": -10, "y": -100},
            "reload_interval_ms": 5000,
            "config_reload_interval_ms": 2000
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=4)
        return default
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    os.makedirs(CONFIG_FOLDER, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class Configurator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Overlay Configurator")
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        mw = self.config["main_window"]
        ow = self.config["overlay_window"]

        self.main_url = QLineEdit(mw.get("url", ""))
        self.main_user = QLineEdit(mw.get("username", ""))
        self.main_pass = QLineEdit(mw.get("password", ""))
        self.main_pass.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow(QLabel("<b>Main Window</b>"))
        layout.addRow("URL:", self.main_url)
        layout.addRow("Username:", self.main_user)
        layout.addRow("Password:", self.main_pass)

        self.overlay_url = QLineEdit(ow.get("url", ""))
        self.width = QSpinBox(); self.width.setRange(100,2000); self.width.setValue(ow.get("width",610))
        self.height = QSpinBox(); self.height.setRange(100,2000); self.height.setValue(ow.get("height",600))
        self.x = QSpinBox(); self.x.setRange(-2000,2000); self.x.setValue(ow.get("x",-10))
        self.y = QSpinBox(); self.y.setRange(-2000,2000); self.y.setValue(ow.get("y",-100))

        layout.addRow(QLabel("<b>Overlay Window</b>"))
        layout.addRow("URL:", self.overlay_url)
        layout.addRow("Width:", self.width)
        layout.addRow("Height:", self.height)
        layout.addRow("X offset:", self.x)
        layout.addRow("Y offset:", self.y)

        self.reload_interval = QSpinBox(); self.reload_interval.setRange(1000,60000); self.reload_interval.setValue(self.config.get("reload_interval_ms",5000))
        self.config_reload_interval = QSpinBox(); self.config_reload_interval.setRange(500,10000); self.config_reload_interval.setValue(self.config.get("config_reload_interval_ms",2000))
        layout.addRow(QLabel("<b>Intervals (ms)</b>"))
        layout.addRow("Reload interval:", self.reload_interval)
        layout.addRow("Config reload interval:", self.config_reload_interval)

        self.save_btn = QPushButton("Save Config")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addRow(self.save_btn)

        self.import_btn = QPushButton("Import JSON Config")
        self.import_btn.clicked.connect(self.import_json)
        layout.addRow(self.import_btn)

        self.setLayout(layout)

    def save_settings(self):
        self.config["main_window"]["url"] = self.main_url.text()
        self.config["main_window"]["username"] = self.main_user.text()
        self.config["main_window"]["password"] = self.main_pass.text()
        self.config["overlay_window"]["url"] = self.overlay_url.text()
        self.config["overlay_window"]["width"] = self.width.value()
        self.config["overlay_window"]["height"] = self.height.value()
        self.config["overlay_window"]["x"] = self.x.value()
        self.config["overlay_window"]["y"] = self.y.value()
        self.config["reload_interval_ms"] = self.reload_interval.value()
        self.config["config_reload_interval_ms"] = self.config_reload_interval.value()
        save_config(self.config)
        QMessageBox.information(self, "Saved", "Configuration saved successfully!")

    def import_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select JSON Config", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, "r") as f:
                imported = json.load(f)

            # Update fields safely
            mw = imported.get("main_window", {})
            ow = imported.get("overlay_window", {})
            self.main_url.setText(mw.get("url", ""))
            self.main_user.setText(mw.get("username", ""))
            self.main_pass.setText(mw.get("password", ""))
            self.overlay_url.setText(ow.get("url", ""))
            self.width.setValue(ow.get("width", 610))
            self.height.setValue(ow.get("height", 600))
            self.x.setValue(ow.get("x", -10))
            self.y.setValue(ow.get("y", -100))
            self.reload_interval.setValue(imported.get("reload_interval_ms", 5000))
            self.config_reload_interval.setValue(imported.get("config_reload_interval_ms", 2000))
            QMessageBox.information(self, "Imported", "JSON configuration imported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import JSON:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Configurator()
    w.show()
    sys.exit(app.exec())