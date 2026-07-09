import sqlite3
import shutil
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "runtime", "backups")

def restore_database(backup_file):
    # Create backup of current database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup = os.path.join(BACKUP_DIR, f"dams_before_restore_{timestamp}.db")
    shutil.copy2(DB_PATH, current_backup)
    
    # Restore from backup
    shutil.copy2(backup_file, DB_PATH)
    
    print(f"Database restored from: {backup_file}")
    print(f"Previous state backed up to: {current_backup}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python restore_database.py <backup_file_path>")
    else:
        restore_database(sys.argv[1])
