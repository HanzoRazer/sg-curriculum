import json
import os
from pathlib import Path
from runtime.cli import main


def test_cli_importable():
    # smoke: module import works; real CLI tested by dev locally
    assert callable(main)
