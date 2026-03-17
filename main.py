import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtCore import QUrl, Qt, QTimer

# Chromium flags
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --ignore-certificate-errors"

# Custom error HTML
CUSTOM_ERROR_HTML = """
<html>
<head><title>Load Error</title></head>
<body style="background-color:#111;color:#fff;text-align:center;font-family:sans-serif;">
    <h1>Oops! Something went wrong.</h1>
    <p>The page could not be loaded.</p>
</body>
</html>
"""

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

class CustomWebPage(QWebEnginePage):
    def __init__(self, profile, parent=None, url=None, reload_interval=5000):
        super().__init__(profile, parent)
        self.url_to_load = url
        self.reload_interval = reload_interval
        self.reload_timer = QTimer()
        self.reload_timer.setSingleShot(True)
        self.reload_timer.timeout.connect(self.try_reload)

    def certificateError(self, error):
        error.acceptCertificate()
        return True

    def handle_load_finished(self, success):
        if not success:
            self.setHtml(CUSTOM_ERROR_HTML)
            if self.url_to_load:
                self.reload_timer.start(self.reload_interval)

    def try_reload(self):
        if self.url_to_load:
            self.load(QUrl(self.url_to_load))


def main_app():
    app = QApplication(sys.argv)

    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    storage_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "web_cache"))
    os.makedirs(storage_path, exist_ok=True)

    profile = QWebEngineProfile("MainProfile")
    profile.setHttpUserAgent(agent)
    profile.setPersistentStoragePath(storage_path)
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
    )

    # -------- MAIN WINDOW --------
    config = load_config()
    main_conf = config.get("main_window", {})
    main_url = main_conf.get("url")
    main_user = main_conf.get("username", "")
    main_pass = main_conf.get("password", "")
    reload_interval = config.get("reload_interval_ms", 5000)

    if main_user and main_pass:
        protocol_sep = "://"
        main_url = main_url.replace(protocol_sep, f"{protocol_sep}{main_user}:{main_pass}@", 1)

    main_view = QWebEngineView()
    main_page = CustomWebPage(profile, main_view, main_url, reload_interval)
    main_view.setPage(main_page)
    main_page.loadFinished.connect(main_page.handle_load_finished)
    main_view.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    main_view.showFullScreen()
    main_view.setHtml("<html><body></body></html>")
    QTimer.singleShot(50, lambda: main_view.load(QUrl(main_url)))

    # -------- OVERLAY WINDOW --------
    overlay_view = QWebEngineView()
    overlay_page = CustomWebPage(profile, overlay_view, config.get("overlay_window", {}).get("url"), reload_interval)
    overlay_view.setPage(overlay_page)
    overlay_page.loadFinished.connect(overlay_page.handle_load_finished)

    overlay_view.setWindowFlags(
        Qt.WindowType.FramelessWindowHint |
        Qt.WindowType.WindowStaysOnTopHint |
        Qt.WindowType.Tool
    )
    overlay_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    overlay_view.setStyleSheet("background: transparent;")

    def hide_scrollbars():
        overlay_view.page().runJavaScript("""
            document.body.style.overflow='hidden';
            document.documentElement.style.overflow='hidden';
            document.body.style.background='transparent';
        """)

    overlay_view.loadFinished.connect(hide_scrollbars)

    def apply_overlay_config():
        cfg = load_config().get("overlay_window", {})
        width = cfg.get("width", 610)
        height = cfg.get("height", 600)
        x_offset = cfg.get("x", -10)
        y_offset = cfg.get("y", -100)
        overlay_view.resize(width, height)
        screen = app.primaryScreen().availableGeometry()
        x = screen.width() - width + x_offset
        y = screen.height() - height + y_offset
        overlay_view.move(x, y)

    # Timer to reload overlay config live
    config_reload_interval = config.get("config_reload_interval_ms", 2000)
    config_timer = QTimer()
    config_timer.timeout.connect(apply_overlay_config)
    config_timer.start(config_reload_interval)

    overlay_view.setHtml("<html><body></body></html>")
    QTimer.singleShot(50, lambda: overlay_view.load(QUrl(config.get("overlay_window", {}).get("url"))))
    overlay_view.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main_app()
    except Exception as e:
        print("Critical startup error:", e)