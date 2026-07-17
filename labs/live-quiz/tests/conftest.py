# tests/conftest.py — pytest loads conftest before any test module, so this runs first.
#
# Two jobs, both about `import app` now having import-time side effects (it opens SQLite and reads
# DB_PATH / INVITE_CODE / SECRET_KEY at module top):
#
# 1) Set safe throwaway env defaults BEFORE app is ever imported, so a bare `import app` never
#    tries to create/write the container's root-owned /data dir. init_db is idempotent, so reusing
#    one file across tests is fine. Individual tests still override with monkeypatch.setenv(...) +
#    importlib.reload(app) (setdefault yields to an already-set value).
#
# 2) Undo cross-test contamination from importlib.reload(app). Several tests reload `app` to pick
#    up patched env; reload re-executes the module and rebinds its singletons (app, socketio,
#    GAMES, the DB connection) to brand-new objects. Other test files captured the ORIGINAL
#    objects via `from app import app, GAMES` at collection time, so after a reload their view of
#    the module goes stale (e.g. a route writes to the new GAMES while the test asserts on the old
#    one). An autouse fixture restores the pristine singletons after every test.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

os.environ.setdefault("DB_PATH", "/tmp/lq-test-conftest.db")
os.environ.setdefault("INVITE_CODE", "TESTINVITE")
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest  # noqa: E402
import app as _app_module  # noqa: E402  (import here, after env defaults, to be app's first importer)

# Module-level singletons captured at the first clean import. Names that don't exist yet (e.g. a
# later task's GAME_OWNER) are simply skipped.
_SINGLETON_NAMES = (
    "app", "socketio", "GAMES", "SID_TO_PLAYER", "CURRENT_SID",
    "_conn", "INVITE_CODE", "DB_PATH", "GAME_OWNER",
)
_PRISTINE = {name: getattr(_app_module, name) for name in _SINGLETON_NAMES if hasattr(_app_module, name)}


@pytest.fixture(autouse=True)
def _restore_app_singletons_after_reload():
    yield
    mod = sys.modules.get("app")
    if mod is None:
        return
    for name, obj in _PRISTINE.items():
        setattr(mod, name, obj)
