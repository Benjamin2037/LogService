import os
from pathlib import Path

from cryptography.fernet import Fernet

from backend.storage import LocalStore


def test_storage_encrypt_roundtrip(tmp_path: Path):
    key = Fernet.generate_key().decode("utf-8")
    os.environ["LOGSERVICE_MASTER_KEY"] = key

    store = LocalStore(tmp_path)
    store.save_json("auth", "token1", {"token": "abc"}, encrypt=True)
    loaded = store.load_json("auth", "token1", decrypt=True)
    assert loaded["token"] == "abc"
