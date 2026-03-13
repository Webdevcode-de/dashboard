import sys
import os
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

# Reload interval in milliseconds
RELOAD_INTERVAL = 5000  # 5 seconds


class CustomWebPage(QWebEnginePage):
    def __init__(self, profile, parent=None, url=None):
        super().__init__(profile, parent)
        self.url_to_load = url
        self.reload_timer = QTimer()
        self.reload_timer.setSingleShot(True)
        self.reload_timer.timeout.connect(self.try_reload)

    def certificateError(self, error):
        # Accept all certificate errors
        error.acceptCertificate()
        return True

    def handle_load_finished(self, success):
        if not success:
            # Show custom error page
            self.setHtml(CUSTOM_ERROR_HTML)
            # Schedule a reload
            if self.url_to_load:
                self.reload_timer.start(RELOAD_INTERVAL)

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
    main_view = QWebEngineView()
    main_url = "https://user:pass1@testpages.eviltester.com/pages/auth/basic-auth/basic-auth-results.html"
    main_page = CustomWebPage(profile, main_view, main_url)
    main_view.setPage(main_page)
    main_page.loadFinished.connect(main_page.handle_load_finished)

    main_view.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    main_view.showFullScreen()

    main_view.setHtml("<html><body></body></html>")  # blank page first
    QTimer.singleShot(50, lambda: main_view.load(QUrl(main_url)))

    # -------- OVERLAY WINDOW --------
    overlay_view = QWebEngineView()
    overlay_url = "http://localhost:8000"
    overlay_page = CustomWebPage(profile, overlay_view, overlay_url)
    overlay_view.setPage(overlay_page)
    overlay_page.loadFinished.connect(overlay_page.handle_load_finished)

    overlay_view.resize(610, 600)
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

    def position_overlay():
        screen = app.primaryScreen().availableGeometry()
        x = screen.width() - overlay_view.width() - 10
        y = screen.height() - overlay_view.height() + 100
        overlay_view.move(x, y)

    position_overlay()
    move_timer = QTimer()
    move_timer.timeout.connect(position_overlay)
    move_timer.start(2000)

    overlay_view.setHtml("<html><body></body></html>")  # blank page first
    QTimer.singleShot(50, lambda: overlay_view.load(QUrl(overlay_url)))
    overlay_view.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main_app()
    except Exception as e:
        print("Critical startup error:", e)
