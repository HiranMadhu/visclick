"""``python -m visclick`` → launch the GUI.

For the headless CLI use ``python -m visclick.bot --instruction "..."``.
"""
from visclick.gui import main

if __name__ == "__main__":
    raise SystemExit(main())
