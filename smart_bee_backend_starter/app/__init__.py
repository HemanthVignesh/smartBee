# Ensure virtualenv site-packages is in sys.path (needed for multiprocessing on macOS)
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir:
    if os.path.exists(os.path.join(current_dir, "venv")):
        venv_dir = os.path.join(current_dir, "venv")
        # Find site-packages directory
        lib_dir = os.path.join(venv_dir, "lib")
        if os.path.exists(lib_dir):
            for py_dir in os.listdir(lib_dir):
                sp = os.path.join(lib_dir, py_dir, "site-packages")
                if os.path.exists(sp) and sp not in sys.path:
                    sys.path.insert(0, sp)
        sp_win = os.path.join(venv_dir, "Lib", "site-packages")
        if os.path.exists(sp_win) and sp_win not in sys.path:
            sys.path.insert(0, sp_win)
        break
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent

# Monkeypatch importlib.metadata to prevent slow filesystem scanning/crawling which hangs Pydantic/Uvicorn/SQLAlchemy/Alembic startup on macOS
import importlib.metadata

class MockEntryPoints(tuple):
    def select(self, *args, **kwargs):
        return MockEntryPoints()

importlib.metadata.distributions = lambda *args, **kwargs: []
importlib.metadata.entry_points = lambda *args, **kwargs: MockEntryPoints()
