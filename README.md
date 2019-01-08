# chrome-decrypter

Python script to decrypt saved Chrome usernames and passwords on windows

## Setup

### Python dependencies

Python 3.6 and:

    python -m pip install pipenv

### chrome-decrypter dependencies to run and build

    pipenv install

## Run

    pipenv run python chrome_decrypt.py

## Build .exe

    pipenv run pyinstaller --clean -F --distpath=. chrome_decrypt.py
