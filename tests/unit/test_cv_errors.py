"""
Tests for the diagnosis of controlled vocabulary database errors.
"""

import sqlite3

from sqlalchemy.exc import MultipleResultsFound

from esgprep._exceptions import CVDatabaseError
from esgprep._utils.cv import find_duplicated_terms, is_cv_database_error


def _make_db(path, terms):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE pcollections (pk INTEGER PRIMARY KEY, id VARCHAR)")
        conn.execute("CREATE TABLE pterms (pk INTEGER PRIMARY KEY, id VARCHAR, collection_pk INTEGER)")
        conn.executemany("INSERT INTO pcollections (pk, id) VALUES (?, ?)", [(1, "version"), (2, "variable_id")])
        conn.executemany("INSERT INTO pterms (id, collection_pk) VALUES (?, ?)", terms)


def test_find_duplicated_terms(tmp_path):
    db = tmp_path / "cv.db"
    _make_db(db, [("creationdate", 1), ("creationdate", 1), ("tas", 2), ("tasis", 2), ("tasis", 2)])
    assert find_duplicated_terms(str(db)) == [("variable_id", "tasis", 2), ("version", "creationdate", 2)]


def test_find_duplicated_terms_clean_or_unreadable_db(tmp_path):
    db = tmp_path / "cv.db"
    _make_db(db, [("creationdate", 1), ("tas", 2)])
    assert find_duplicated_terms(str(db)) == []
    assert find_duplicated_terms(str(tmp_path / "missing.db")) == []


def test_is_cv_database_error():
    assert is_cv_database_error(MultipleResultsFound("dup"))
    assert not is_cv_database_error(ValueError("bad attribute"))


def test_cv_database_error_message():
    duplicates = [("variable_id", f"var{i}", 2) for i in range(12)]
    msg = str(CVDatabaseError("cmip6", "2.1.0", "/db/cmip6/2.1.0.db", MultipleResultsFound("dup"), duplicates))
    assert "not caused by your files" in msg
    assert "<CV version: '2.1.0'>" in msg
    assert "MultipleResultsFound" in msg
    assert "12 duplicated term(s)" in msg
    assert "variable_id/var9" in msg and "variable_id/var10" not in msg
    assert "... and 2 more" in msg
    assert "esgvoc use cmip6@<version>" in msg
