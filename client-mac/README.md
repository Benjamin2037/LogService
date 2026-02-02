# LogService macOS Client

Lightweight desktop wrapper for the local LogService UI.

## Requirements
- Python 3.11+
- LogService backend running on `127.0.0.1:8000`

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

## Notes
- This client only connects to `http://127.0.0.1:8000/ui`.
- The backend should be started with `--host 127.0.0.1` for safety.
