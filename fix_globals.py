import os

APP_DIR = r"d:\MYPRO\DC\DC_Manager"
py_path = os.path.join(APP_DIR, "DC_WebApp.py")

with open(py_path, 'r', encoding='utf-8') as f:
    py_content = f.read()

# Remove from inside create_app
bad_block = """    # --- TRAFFIC AND SUBSCRIPTION CONTROL ---
    MAX_ACTIVE_GUESTS = 5
    GUEST_SESSION_TIMEOUT_MINUTES = 10
    ACTIVE_GUEST_SESSIONS = {}  # Format: { session_id: last_active_timestamp }

    import time
    import uuid
    from datetime import datetime"""

py_content = py_content.replace(bad_block, "")

# Insert at the top of the file after standard imports
good_block = """import time
import uuid

# --- TRAFFIC AND SUBSCRIPTION CONTROL ---
MAX_ACTIVE_GUESTS = 5
GUEST_SESSION_TIMEOUT_MINUTES = 10
ACTIVE_GUEST_SESSIONS = {}  # Format: { session_id: last_active_timestamp }
"""

py_content = py_content.replace("import tempfile", "import tempfile\n" + good_block)

# Also fix the indentation of track_guest_sessions if it's messed up
# It's currently inside create_app, which is fine, but it accesses ACTIVE_GUEST_SESSIONS globally now.

with open(py_path, 'w', encoding='utf-8') as f:
    f.write(py_content)

print("Fixed globals")
