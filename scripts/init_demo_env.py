"""Create local demo credentials once; never print or overwrite secrets."""

import os
import secrets
from pathlib import Path

path = Path(__file__).resolve().parents[1] / ".env.demo"
try:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env.demo already exists; preserved existing credentials.")
with os.fdopen(descriptor, "w") as output:
    output.write("DEMO_DB_PASSWORD=" + secrets.token_hex(24) + "\n")
    output.write("DEMO_JWT_SECRET=" + secrets.token_hex(32) + "\n")
print("Created ignored .env.demo with local-only credentials.")
