import os
import subprocess
import sys
import unittest
from pathlib import Path


@unittest.skipUnless(
    os.getenv("RUN_INTEGRATION") == "1", "Start compose.test.yaml and set RUN_INTEGRATION=1"
)
class PersistenceIntegrationTests(unittest.TestCase):
    def test_real_postgres_and_redis(self):
        root = Path(__file__).resolve().parents[1]
        subprocess.run(
            [sys.executable, str(root / "scripts/verify_isolated.py")], cwd=root, check=True
        )
