import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtCore import QUrl, Qt, QTimer

CONFIG_FOLDER = os.path.join(os.path.expanduser("~"), ".screenapp")
CONFIG_FILE = os.path.join(CONFIG_FOLDER, "config.json")

CUSTOM_ERROR_HTML = """
<html>
<head><title>Load Error</title></head>
<body style="background-color:#111;color:#fff;text-align:center;font-family:sans-serif;">
<h1>Oops! Something went wrong.</h1>
<p>The page could not be loaded.</p>
</body>
</html>
"""

def load_config():
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
    config = load_config()

    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    profile = QWebEngineProfile("MainProfile")
    profile.setHttpUserAgent(agent)
    profile.setPersistentStoragePath(os.path.join(CONFIG_FOLDER, "web_cache"))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

    # Main window
    main_conf = config.get("main_window", {})
    main_url = main_conf.get("url", "")
    user = main_conf.get("username", "")
    pw = main_conf.get("password", "")
    if user and pw:
        main_url = main_url.replace("://", f"://{user}:{pw}@", 1)

    main_view = QWebEngineView()
    main_page = CustomWebPage(profile, main_view, main_url, config.get("reload_interval_ms",5000))
    main_view.setPage(main_page)
    main_page.loadFinished.connect(main_page.handle_load_finished)
    main_view.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    main_view.showFullScreen()
    main_view.setHtml("<html><body></body></html>")
    QTimer.singleShot(50, lambda: main_view.load(QUrl(main_url)))

    # Overlay window
    overlay_view = QWebEngineView()
    overlay_page = CustomWebPage(profile, overlay_view, config.get("overlay_window", {}).get("url",""), config.get("reload_interval_ms",5000))
    overlay_view.setPage(overlay_page)
    overlay_page.loadFinished.connect(overlay_page.handle_load_finished)

    overlay_view.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
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
        overlay_view.resize(cfg.get("width",610), cfg.get("height",600))
        screen = app.primaryScreen().availableGeometry()
        x = screen.width() - cfg.get("width",610) + cfg.get("x",-10)
        y = screen.height() - cfg.get("height",600) + cfg.get("y",-100)
        overlay_view.move(x,y)

    config_timer = QTimer()
    config_timer.timeout.connect(apply_overlay_config)
    config_timer.start(config.get("config_reload_interval_ms",2000))

    overlay_view.setHtml("<html><body></body></html>")
    QTimer.singleShot(50, lambda: overlay_view.load(QUrl(config.get("overlay_window", {}).get("url",""))))
    overlay_view.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main_app()
    except Exception as e:
        print("Critical startup error:", e)