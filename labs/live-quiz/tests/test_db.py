import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import db


def _fresh(tmp_path):
    d = db.connect(str(tmp_path / "t.db"))
    db.init_db(d)
    return d


def test_init_is_idempotent(tmp_path):
    p = str(tmp_path / "t.db")
    db.init_db(db.connect(p)); db.init_db(db.connect(p))  # second call must not raise


def test_create_and_get_teacher(tmp_path):
    d = _fresh(tmp_path)
    tid = db.create_teacher(d, "alice", "hash1", now="2026-01-01")
    t = db.get_teacher_by_username(d, "alice")
    assert t["id"] == tid and t["password_hash"] == "hash1"


def test_duplicate_username_rejected(tmp_path):
    d = _fresh(tmp_path)
    db.create_teacher(d, "alice", "h", now="t")
    try:
        db.create_teacher(d, "alice", "h2", now="t")
        assert False, "expected an integrity error on duplicate username"
    except Exception:
        pass


def test_set_crud_and_owner_isolation(tmp_path):
    d = _fresh(tmp_path)
    a = db.create_teacher(d, "alice", "h", now="t")
    b = db.create_teacher(d, "bob", "h", now="t")
    sid = db.create_set(d, a, "W1", "## T\n1. q a) x ✓ · b) y", now="t")
    assert [s["title"] for s in db.list_sets(d, a)] == ["W1"]
    assert db.list_sets(d, b) == []                       # bob sees nothing
    assert db.get_set(d, sid, owner_id=a)["source_md"].startswith("## T")
    assert db.get_set(d, sid, owner_id=b) is None         # IDOR-safe: not bob's
    db.update_set(d, sid, owner_id=a, title="W1b", source_md="## T2\n1. q a) x ✓ · b) y", now="t2")
    assert db.get_set(d, sid, owner_id=a)["title"] == "W1b"
    assert db.update_set(d, sid, owner_id=b, title="hax", source_md="## X", now="t3") == 0  # bob can't edit alice's
    assert db.get_set(d, sid, owner_id=a)["title"] == "W1b"                                 # unchanged
    assert db.delete_set(d, sid, owner_id=b) == 0         # bob can't delete alice's
    assert db.delete_set(d, sid, owner_id=a) == 1
    assert db.get_set(d, sid, owner_id=a) is None


def test_delete_teacher_cascades_sets(tmp_path):
    # pins ON DELETE CASCADE, which is only active because connect() sets PRAGMA foreign_keys=ON;
    # without this test, dropping that pragma would silently orphan every teacher's sets.
    d = _fresh(tmp_path)
    a = db.create_teacher(d, "alice", "h", now="t")
    db.create_set(d, a, "W1", "## T\n1. q a) x ✓ · b) y", now="t")
    d.execute("DELETE FROM teachers WHERE id = ?", (a,)); d.commit()
    assert d.execute("SELECT COUNT(*) FROM question_sets").fetchone()[0] == 0
