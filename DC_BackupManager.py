import json
import os
import shutil
from datetime import datetime

from DC_DataLoader import BACKUP_DIR


class DCBackupManager:
    def __init__(self, dc_file):
        self.dc_file = dc_file
        self.backup_dir = BACKUP_DIR
        self.manifest_file = os.path.join(self.backup_dir, "manifest.json")

    def backup(self, reason="manual"):
        if not os.path.exists(self.dc_file):
            raise FileNotFoundError(f"Source workbook not found: {self.dc_file}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"dc_backup_{timestamp}.xlsx")
        shutil.copy2(self.dc_file, backup_path)
        manifest = self.list_backups()
        manifest.append(
            {
                "path": backup_path,
                "filename": os.path.basename(backup_path),
                "time": datetime.now().isoformat(),
                "size_mb": round(os.path.getsize(backup_path) / 1024 / 1024, 2),
                "reason": reason,
            }
        )
        with open(self.manifest_file, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
        return backup_path

    def list_backups(self):
        if not os.path.exists(self.manifest_file):
            return []
        with open(self.manifest_file, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
