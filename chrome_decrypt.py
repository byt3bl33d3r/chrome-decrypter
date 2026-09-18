"""Legacy Windows DPAPI reader; no support for modern Chrome encryption schemes."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
import sys


def decrypt_legacy(value):
    # Keep the historical DPAPI method; importing this module has no OS side effects.
    import win32crypt
    return win32crypt.CryptUnprotectData(value, None, None, None, 0)[1]


def display_rows(rows, decrypt, out, err):
    """Return the number of failed rows without reusing a previous row's value."""
    failed = 0
    for number, (url, username, encrypted) in enumerate(rows, 1):
        try:
            password = decrypt(encrypted)
            if isinstance(password, bytes):
                password = password.decode('utf-8', errors='backslashreplace')
        except Exception:
            # Exception messages from a provider may contain sensitive input.
            print('[-] Unable to decrypt row {}.'.format(number), file=err)
            failed += 1
            continue
        if password:
            print('[+] URL: {}\n    Username: {}\n    Password: {}'.format(
                url, username, password), file=out)
    return failed


def main(argv=None, decrypt=None, out=None, err=None):
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path,
                        help='Explicit path to a database you are authorized to read')
    args = parser.parse_args(argv)
    if not args.database.is_file():
        print('[-] Database file does not exist.', file=err)
        return 1
    try:
        # A typo must never create an empty database or modify the input file.
        uri = args.database.resolve().as_uri() + '?mode=ro'
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            rows = connection.execute(
                'SELECT action_url, username_value, password_value FROM logins')
            failures = display_rows(rows, decrypt or decrypt_legacy, out, err)
    except sqlite3.Error:
        print('[-] Unable to read the login table.', file=err)
        return 1
    return 2 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
