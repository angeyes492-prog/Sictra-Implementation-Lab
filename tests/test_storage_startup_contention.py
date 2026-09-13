import sqlite3
import unittest
from unittest.mock import Mock, patch

from sictra_block1.storage import OperationalStore


class StartupContentionTests(unittest.TestCase):
    def test_busy_wal_transition_retries_then_succeeds(self):
        error = sqlite3.OperationalError('database is locked')
        error.sqlite_errorcode = sqlite3.SQLITE_BUSY
        store = OperationalStore.__new__(OperationalStore)
        store._db = Mock()
        store._db.execute.side_effect = [error, None]
        with patch('sictra_block1.storage.sleep') as pause:
            store._enable_wal()
        self.assertEqual(2, store._db.execute.call_count)
        pause.assert_called_once_with(0.05)

    def test_non_lock_failure_and_exhausted_deadline_are_not_hidden(self):
        for code in (sqlite3.SQLITE_READONLY, sqlite3.SQLITE_BUSY):
            with self.subTest(code=code):
                error = sqlite3.OperationalError('failure')
                error.sqlite_errorcode = code
                store = OperationalStore.__new__(OperationalStore)
                store._db = Mock()
                store._db.execute.side_effect = error
                with patch('sictra_block1.storage.monotonic', side_effect=[0,31]), patch('sictra_block1.storage.sleep') as pause:
                    with self.assertRaises(sqlite3.OperationalError):
                        store._enable_wal()
                pause.assert_not_called()
