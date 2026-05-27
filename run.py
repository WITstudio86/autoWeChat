import webbrowser
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    app = create_app()
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True, port=5000)
