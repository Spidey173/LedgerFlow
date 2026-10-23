import pytest
import sqlite3
import pandas as pd
from unittest.mock import MagicMock, patch

from scripts.load_postgres import create_staging_tables, drop_staging_tables, atomic_swap_tables
import scripts.load_postgres as loader

def test_staging_tables_lifecycle():
    """Verify that staging tables are created and cleanly dropped."""
    mock_cursor = MagicMock()
    tables = ["branches", "customers"]
    
    create_staging_tables(mock_cursor, tables)
    assert mock_cursor.execute.call_count == 4  # 2 drops + 2 creates

    mock_cursor.reset_mock()
    drop_staging_tables(mock_cursor, tables)
    assert mock_cursor.execute.call_count == 2

def test_atomic_swap_executes_in_order():
    """Verify that atomic swap clears live tables in reverse order and inserts forward."""
    mock_cursor = MagicMock()
    tables = ["branches", "customers", "accounts"]
    
    # 1. Test Default Non-Blocking MVCC Swap (DELETE)
    atomic_swap_tables(mock_cursor, tables, use_truncate=False)

    calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
    # Reverse non-blocking deletion
    assert "DELETE FROM accounts;" in calls[0]
    assert "DELETE FROM customers;" in calls[1]
    assert "DELETE FROM branches;" in calls[2]

    # Forward staged insert
    assert "INSERT INTO branches SELECT * FROM stg_branches;" in calls[3]
    assert "INSERT INTO customers SELECT * FROM stg_customers;" in calls[4]
    assert "INSERT INTO accounts SELECT * FROM stg_accounts;" in calls[5]

    # 2. Test Optional Truncate Mode
    mock_cursor.reset_mock()
    atomic_swap_tables(mock_cursor, tables, use_truncate=True)
    truncate_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
    assert "TRUNCATE TABLE accounts CASCADE;" in truncate_calls[0]
    assert "TRUNCATE TABLE customers CASCADE;" in truncate_calls[1]
    assert "TRUNCATE TABLE branches CASCADE;" in truncate_calls[2]

def test_concurrent_run_prevention_via_advisory_lock(monkeypatch):
    """Verify that if an advisory lock cannot be acquired, the loader aborts immediately."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Simulate lock acquisition failure (already held by another worker)
    mock_cursor.fetchone.return_value = [False]
    monkeypatch.setattr(loader, "get_connection", lambda: mock_conn)
    monkeypatch.setattr(loader, "validate_db_credentials", lambda raise_on_missing=True: True)
    # Ensure test does not depend on local CSV files being present on disk
    monkeypatch.setattr(loader.os.path, "exists", lambda p: True)

    with pytest.raises(RuntimeError) as exc_info:
        loader.load_all_curated_data()

    assert "Another pipeline refresh operation is currently in progress" in str(exc_info.value)
    # Ensure rollback is triggered on failure
    mock_conn.rollback.assert_called_once()

