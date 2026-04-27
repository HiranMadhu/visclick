"""
Hotkey screenshot capture on Windows. Run terminal as Administrator for global F9.
See VisClick_Detailed_Plan.md Part E.
"""
import datetime
import os
import time

import mss

try:
    import keyboard
except ImportError:
    raise SystemExit("pip install keyboard mss") from None

APP_KEY_TO_NAME = {"1": "vscode", "2": "file_explorer", "3": "chrome", "4": "notepad"}
out_root = os.path.expanduser(r"~\Documents\visclick_data\desktop_unlabeled")


def capture(app: str) -> str:
    folder = os.path.join(out_root, app)
    os.makedirs(folder, exist_ok=True)
    name = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ.png")
    path = os.path.join(folder, name)
    with mss.mss() as sct:
        sct.shot(mon=-1, output=path)
    return path


def main() -> None:
    print("Press 1/2/3/4 to choose app, then F9 to capture, F10 to quit.")
    app = "vscode"
    while True:
        if keyboard.is_pressed("f10"):
            break
        for k, v in APP_KEY_TO_NAME.items():
            if keyboard.is_pressed(k):
                app = v
                print("active:", app)
                time.sleep(0.4)
        if keyboard.is_pressed("f9"):
            path = capture(app)
            print("saved", path)
            time.sleep(0.4)
        time.sleep(0.05)


if __name__ == "__main__":
    main()
