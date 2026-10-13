# -*- coding: utf-8 -*-

"""
:platform: Unix
:synopsis: Diagnostics for errors raised by the esgvoc controlled vocabulary databases.

"""

import sqlite3

from sqlalchemy.exc import SQLAlchemyError

from esgprep._exceptions import CVDatabaseError


def active_cv_info(project: str) -> dict | None:
    """
    Returns esgvoc information about the active database of a project (version, source, path).

    """
    try:
        import esgvoc.api as ev

        return ev.get_active_database_info(project)
    except Exception:
        return None


def find_duplicated_terms(db_path: str) -> list[tuple[str, str, int]]:
    """
    Returns the (collection, term, count) triplets that appear more than once in a project database.
    A term must be unique within its collection: duplicates make esgvoc term lookups fail.

    """
    query = (
        "SELECT c.id, t.id, COUNT(*) FROM pterms t "
        "JOIN pcollections c ON t.collection_pk = c.pk "
        "GROUP BY c.id, t.id HAVING COUNT(*) > 1 ORDER BY c.id, t.id"
    )
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            return conn.execute(query).fetchall()
    except sqlite3.Error:
        return []


def is_cv_database_error(error: BaseException) -> bool:
    """
    Whether an exception originates from the controlled vocabulary database rather than the input data.

    """
    from esgvoc.core.exceptions import EsgvocDbError

    return isinstance(error, (SQLAlchemyError, EsgvocDbError))


def diagnose_cv_error(project: str, error: BaseException) -> CVDatabaseError:
    """
    Builds a CVDatabaseError describing the active CV database and its known defects.

    """
    info = active_cv_info(project) or {}
    duplicates = find_duplicated_terms(info["path"]) if info.get("path") else []
    return CVDatabaseError(project, info.get("version"), info.get("path"), error, duplicates)
