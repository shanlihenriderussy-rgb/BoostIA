"""Point d'entrée pour le .exe PyInstaller.

Lance le serveur uvicorn et ouvre le navigateur sur http://127.0.0.1:8000.
"""

from __future__ import annotations

import sys
import threading
import time
import webbrowser

import uvicorn


HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def _open_browser_when_ready() -> None:
    time.sleep(1.5)
    webbrowser.open(URL)


def main() -> None:
    print("=" * 56)
    print("  BoostIA - Assistant de redaction local")
    print("=" * 56)
    print(f"  Serveur : {URL}")
    print("  Pour quitter : fermez cette fenetre (Ctrl+C)")
    print("=" * 56)

    threading.Thread(target=_open_browser_when_ready, daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nArret de BoostIA.")
        sys.exit(0)
