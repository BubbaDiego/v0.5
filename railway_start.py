#!/usr/bin/env python
"""
railway_start.py

Startup wrapper for Railway deployments.
Copies the initial DB and config into the persistent volume on first deploy,
then launches the main app.
"""

import os
import shutil

VOLUME_PATH = "/data"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_TO_PERSIST = [
    ("data/mother_brain.db", "mother_brain.db"),
    ("sonic_config.json", "sonic_config.json"),
]


def seed_volume():
    """Copy repo copies into the volume only if they don't already exist."""
    os.makedirs(VOLUME_PATH, exist_ok=True)
    for repo_rel, vol_name in FILES_TO_PERSIST:
        src = os.path.join(REPO_DIR, repo_rel)
        dst = os.path.join(VOLUME_PATH, vol_name)
        if not os.path.exists(dst) and os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"[railway_start] Seeded {dst} from {src}")
        else:
            print(f"[railway_start] {dst} already exists, skipping seed")


if __name__ == "__main__":
    seed_volume()

    # Now launch the real app
    import launch_pad
    launch_pad.socketio.run(
        launch_pad.app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
    )
