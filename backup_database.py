import sqlite3
import shutil
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "runtime", "backups")

def backup_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"dams_backup_{timestamp}.db")
    
    # Copy database file
    shutil.copy2(DB_PATH, backup_path)
    
    print(f"Database backed up to: {backup_path}")
    return backup_path

if __name__ == "__main__":
    backup_database()
