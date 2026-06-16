import os
import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Create required directories
dirs = ["uploads", "uploads/.tmp"]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)
    print(f"[OK] Created: {d}/")

# Copy .env.example if .env doesn't exist
if not Path(".env").exists() and Path(".env.example").exists():
    import shutil
    shutil.copy(".env.example", ".env")
    print("[OK] Copied .env.example -> .env")
    print("[WARN] Edit .env with your actual credentials before running the server!")
else:
    print("[OK] .env already exists")

print("\n[DONE] Setup complete! Run:")
print("   uvicorn app.main:app --reload --port 8000")
print("   celery -A app.workers.celery_app worker --loglevel=info -P threads")
