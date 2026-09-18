# chrome-decrypter (legacy)

Historical Windows/Python code for reading saved Chrome credentials. The historical
Pipfile targets Python 3.6. The control-flow tests below use current Python, but
compatibility with current Chrome encryption has not been verified. This repository should not be treated as a supported
password-recovery utility.

## Access your own saved passwords

Use [Google Password Manager in Chrome](https://support.google.com/chrome/answer/95606)
to view and manage your passwords, or follow Google's official
[import/export instructions](https://support.google.com/chrome/answer/13068232).
An exported password file contains plaintext secrets: keep it private and remove
it after the intended import. Do not add exported data to this repository.

## Repository status

- The historical source is `chrome_decrypt.py`. Row-failure handling, database
  lifecycle, and CLI path selection have been corrected. The original DPAPI call
  is unchanged; no support for newer browser protection schemes is added.
- `Pipfile` and `Pipfile.lock` describe the historical environment. They are retained
  for provenance, not as a recommendation to install Python 3.6 today.
- The checked-in executable has been removed from the current tree. Its provenance
  and behavior were not verified in this maintenance pass; old Git commits still
  contain it. No executable was run to review this change.
- Generated executables, build directories, virtual environments, and typical
  credential exports are excluded from future commits via `.gitignore`.

## Logic tests

```sh
python -m unittest discover -s tests -v
```

Tests use temporary SQLite databases and injected fake decryptors. They do not
read a browser profile, call native decryption, or require pywin32. They cover a
failed first row, failure after a successful row, Unicode/empty values, a missing
file, read-only access, connection cleanup, and partial-failure exit status.

## CLI behavior change

The CLI now requires an explicit database path; it no longer scans the user
profile. Importing the module does not open files or load native decryption.
SQLite opens only existing files in read-only mode. Status 0 means no row failures,
1 means a database error, and 2 means one or more rows could not be decrypted.
Argument parsing errors also use status 2. Failed rows never print a previous
row's password, and provider exception details are not printed.

There is no current Chrome compatibility claim or supported binary release.
