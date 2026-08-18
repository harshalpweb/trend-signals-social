"""Put scripts/ on sys.path so tests can import the rail modules directly.

The scripts are executed as `python scripts/<name>.py` in CI, which puts
scripts/ on sys.path implicitly; pytest does not, hence this shim.
"""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
