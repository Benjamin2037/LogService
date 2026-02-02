import threading
import time
from typing import Optional

import requests
import webview


HEALTH_URL = "http://127.0.0.1:8000/health"
UI_URL = "http://127.0.0.1:8000/ui"


def wait_for_backend(timeout_seconds: int = 6) -> Optional[str]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            resp = requests.get(HEALTH_URL, timeout=0.5)
            if resp.ok:
                return UI_URL
        except requests.RequestException:
            time.sleep(0.4)
    return None


def create_window() -> None:
    url = wait_for_backend()
    if url:
        webview.create_window(
            "LogService",
            url,
            width=1200,
            height=800,
            confirm_close=True,
        )
        return

    fallback_html = """
    <html>
      <head>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 24px; }
          h1 { margin-top: 0; }
          code { background: #f2f2f2; padding: 2px 6px; border-radius: 6px; }
        </style>
      </head>
      <body>
        <h1>LogService backend not running</h1>
        <p>Start the backend first:</p>
        <p><code>uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000</code></p>
      </body>
    </html>
    """
    webview.create_window(
        "LogService",
        html=fallback_html,
        width=900,
        height=600,
        confirm_close=True,
    )


if __name__ == "__main__":
    threading.Thread(target=create_window, daemon=True).start()
    webview.start()
