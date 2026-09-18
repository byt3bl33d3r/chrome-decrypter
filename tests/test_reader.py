"""Synthetic fixtures only: no browser profile or native decryption is accessed."""
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import chrome_decrypt as reader


class ReaderTests(unittest.TestCase):
    def test_failed_first_row_is_not_unbound(self):
        out, err = io.StringIO(), io.StringIO()
        def fail(value):
            raise ValueError('private-provider-input')
        self.assertEqual(reader.display_rows([('fixture', 'user', b'x')], fail, out, err), 1)
        self.assertEqual(out.getvalue(), '')
        self.assertNotIn('private-provider-input', err.getvalue())

    def test_failed_row_never_reuses_previous_plaintext(self):
        out, err = io.StringIO(), io.StringIO()
        def decrypt(value):
            if value == b'bad':
                raise ValueError('fixture failure')
            return value
        rows = [('first.example', 'first', b'fixture-one'),
                ('failed.example', 'failed', b'bad'),
                ('last.example', 'last', b'fixture-last')]
        self.assertEqual(reader.display_rows(rows, decrypt, out, err), 1)
        self.assertEqual(out.getvalue().count('fixture-one'), 1)
        self.assertNotIn('failed.example', out.getvalue())
        self.assertIn('fixture-last', out.getvalue())

    def test_unicode_and_empty_values(self):
        out = io.StringIO()
        rows = [('example', 'fixture', 'آزمایش'.encode()), ('empty', 'fixture', b'')]
        self.assertEqual(reader.display_rows(rows, lambda value: value, out, io.StringIO()), 0)
        self.assertIn('آزمایش', out.getvalue())
        self.assertNotIn('URL: empty', out.getvalue())

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.sqlite'
            self.assertEqual(reader.main([str(path)], out=io.StringIO(), err=io.StringIO()), 1)
            self.assertFalse(path.exists())

    def test_database_is_read_only_and_closed_even_on_query_failure(self):
        original = sqlite3.connect
        opened = []
        def connect(*args, **kwargs):
            connection = original(*args, **kwargs)
            opened.append(connection)
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute('CREATE TABLE forbidden (id)')
            return connection
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture # name.sqlite'
            connection = original(path)
            connection.execute('CREATE TABLE unrelated (id)')
            connection.close()
            with patch.object(reader.sqlite3, 'connect', side_effect=connect):
                self.assertEqual(reader.main([str(path)], out=io.StringIO(), err=io.StringIO()), 1)
            with self.assertRaises(sqlite3.ProgrammingError):
                opened[0].execute('SELECT 1')

    def test_empty_database_and_partial_failure_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.sqlite'
            connection = sqlite3.connect(path)
            connection.execute('CREATE TABLE logins (action_url, username_value, password_value)')
            connection.commit()
            self.assertEqual(reader.main([str(path)], decrypt=lambda value: value,
                                         out=io.StringIO(), err=io.StringIO()), 0)
            connection.execute('INSERT INTO logins VALUES (?, ?, ?)', ('fixture', 'user', b'x'))
            connection.commit()
            connection.close()
            def fail(value):
                raise ValueError('fixture failure')
            self.assertEqual(reader.main([str(path)], decrypt=fail,
                                         out=io.StringIO(), err=io.StringIO()), 2)


if __name__ == '__main__':
    unittest.main()
