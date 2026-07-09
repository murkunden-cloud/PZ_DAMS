# DAMS Database Migration - Step-by-Step Implementation Guide

## Overview
This guide provides detailed actionable steps to convert the Excel-based DAMS system to a database-driven application using SQLite.

---

## PHASE 1: Preparation & Setup

### Step 1.1: Install Required Dependencies
```bash
pip install sqlite3 sqlalchemy pandas openpyxl
```

### Step 1.2: Backup Current Data
```bash
# Create backup directory
mkdir runtime\db_migration_backup

# Backup Excel files
copy origional_35_dc.xlsx runtime\db_migration_backup\
copy master_employe.xlsx runtime\db_migration_backup\
copy config.ini runtime\db_migration_backup\
```

### Step 1.3: Create Database Directory
```bash
mkdir runtime\database
```

---

## PHASE 2: Database Schema Creation

### Step 2.1: Create Database Initialization Script
Create file: `init_database.py`

```python
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create employees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf_no VARCHAR(20) UNIQUE NOT NULL,
        employee_name VARCHAR(200) NOT NULL,
        designation VARCHAR(100),
        present_office VARCHAR(200),
        present_division VARCHAR(100),
        present_circle VARCHAR(100),
        present_zone VARCHAR(100),
        remarks TEXT,
        birth_date DATE,
        retirement_date DATE,
        pay_group VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create disciplinary_cases table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disciplinary_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id VARCHAR(50) UNIQUE NOT NULL,
        case_type VARCHAR(20) NOT NULL CHECK(case_type IN ('minor', 'major', 'suspension', 'appeal')),
        case_status VARCHAR(20) DEFAULT 'active' CHECK(case_status IN ('initiated', 'active', 'closed', 'finalised', 'revoked')),
        sheet_origin VARCHAR(10) NOT NULL,
        scope VARCHAR(20) CHECK(scope IN ('statewise', 'circlewise', 'consolidated')),
        employee_id INTEGER,
        cpf_no VARCHAR(20) NOT NULL,
        employee_name VARCHAR(200) NOT NULL,
        designation VARCHAR(100),
        present_office VARCHAR(200),
        present_division VARCHAR(100),
        present_circle VARCHAR(100),
        present_zone VARCHAR(100),
        dc_number VARCHAR(100),
        dc_date DATE,
        dc_record_number VARCHAR(100),
        dc_record_date DATE,
        facts_of_case TEXT,
        chargesheet_details TEXT,
        enquiry_officer VARCHAR(200),
        punishment_awarded TEXT,
        appeal_details TEXT,
        suspension_start_date DATE,
        suspension_end_date VARCHAR(100),
        suspension_reason TEXT,
        case_closure_date DATE,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by VARCHAR(50),
        updated_by VARCHAR(50),
        FOREIGN KEY (employee_id) REFERENCES employees(id)
    )
    """)
    
    # Create case_history table for audit trail
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS case_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        action_type VARCHAR(50) NOT NULL,
        old_values TEXT,
        new_values TEXT,
        changed_by VARCHAR(50),
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (case_id) REFERENCES disciplinary_cases(id)
    )
    """)
    
    # Create sheet_views table for virtual sheet configurations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sheet_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sheet_name VARCHAR(10) UNIQUE NOT NULL,
        display_name VARCHAR(100) NOT NULL,
        case_type_filter VARCHAR(20),
        case_status_filter VARCHAR(20),
        scope_filter VARCHAR(20),
        class_filter VARCHAR(20),
        column_mapping TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1
    )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_cpf ON disciplinary_cases(cpf_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_type ON disciplinary_cases(case_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_status ON disciplinary_cases(case_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_sheet ON disciplinary_cases(sheet_origin)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_employees_cpf ON employees(cpf_no)")
    
    conn.commit()
    conn.close()
    print(f"Database created successfully at: {DB_PATH}")

if __name__ == "__main__":
    create_database()
```

### Step 2.2: Initialize Database
```bash
python init_database.py
```

### Step 2.3: Populate Sheet Views Configuration
Create file: `populate_sheet_views.py`

```python
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

SHEET_CONFIGURATIONS = [
    {
        "sheet_name": "4DC",
        "display_name": "Minor DC - Statewise (Class I/II)",
        "case_type_filter": "minor",
        "case_status_filter": "initiated",
        "scope_filter": "statewise",
        "class_filter": "I/II",
        "sort_order": 1
    },
    {
        "sheet_name": "5DC",
        "display_name": "Minor DC - Circlewise (Class III/IV)",
        "case_type_filter": "minor",
        "case_status_filter": "initiated",
        "scope_filter": "circlewise",
        "class_filter": "III/IV",
        "sort_order": 2
    },
    # Add all 35 sheet configurations here...
]

def populate_sheet_views():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for config in SHEET_CONFIGURATIONS:
        cursor.execute("""
        INSERT OR REPLACE INTO sheet_views 
        (sheet_name, display_name, case_type_filter, case_status_filter, scope_filter, class_filter, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            config["sheet_name"],
            config["display_name"],
            config["case_type_filter"],
            config["case_status_filter"],
            config["scope_filter"],
            config["class_filter"],
            config["sort_order"]
        ))
    
    conn.commit()
    conn.close()
    print("Sheet views populated successfully")

if __name__ == "__main__":
    populate_sheet_views()
```

---

## PHASE 3: Data Migration

### Step 3.1: Create Employee Data Migration Script
Create file: `migrate_employees.py`

```python
import sqlite3
import pandas as pd
import os
from DC_DataLoader import EMP_FILE, normalize_cpf

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

def migrate_employees():
    # Load employee data from Excel
    emp_df = pd.read_excel(EMP_FILE)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    migrated_count = 0
    for _, row in emp_df.iterrows():
        cpf = normalize_cpf(row.get('CPFNO', ''))
        if not cpf:
            continue
            
        try:
            cursor.execute("""
            INSERT OR REPLACE INTO employees 
            (cpf_no, employee_name, designation, present_office, present_division, 
             present_circle, present_zone, remarks, birth_date, retirement_date, pay_group)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cpf,
                str(row.get('EmployeeName', '')).strip(),
                str(row.get('Designation', '')).strip(),
                str(row.get('PresentOffice', '')).strip(),
                str(row.get('presentDivision', '')).strip(),
                str(row.get('PresentCircle', '')).strip(),
                str(row.get('PresentZone', '')).strip(),
                str(row.get('Remarks', '')).strip(),
                str(row.get('brthdt', '')).strip(),
                str(row.get('dtofretir', '')).strip(),
                str(row.get('paygrp', '')).strip()
            ))
            migrated_count += 1
        except Exception as e:
            print(f"Error migrating employee {cpf}: {e}")
    
    conn.commit()
    conn.close()
    print(f"Migrated {migrated_count} employees to database")

if __name__ == "__main__":
    migrate_employees()
```

### Step 3.2: Create Disciplinary Cases Migration Script
Create file: `migrate_cases.py`

```python
import sqlite3
import pandas as pd
import os
from datetime import datetime
from DC_DataLoader import DC_FILE, META, normalize_cpf, extract_dc, safe_text

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

def migrate_cases():
    # Load Excel file
    excel_file = pd.ExcelFile(DC_FILE)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_migrated = 0
    
    for sheet_name in excel_file.sheet_names:
        if sheet_name not in META:
            continue
            
        meta = META[sheet_name]
        df = pd.read_excel(DC_FILE, sheet_name=sheet_name)
        
        # Skip header rows based on metadata
        df = df.iloc[meta.get("data_start", 0):]
        
        for row_idx, row in df.iterrows():
            try:
                # Extract CPF
                cpf_col = meta.get("cpf_col", 3)
                cpf = normalize_cpf(row.iloc[cpf_col] if cpf_col < len(row) else "")
                if not cpf:
                    continue
                
                # Extract DC number
                dc_col = meta.get("dc_col", 10)
                dc_number = extract_dc(row.iloc[dc_col] if dc_col < len(row) else "")
                
                # Extract facts
                facts_col = meta.get("facts_col", 9)
                facts = safe_text(row.iloc[facts_col] if facts_col < len(row) else "")
                
                # Generate case ID
                case_id = f"{sheet_name}_{cpf}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Determine case type
                case_type = meta.get("type", "minor")
                
                # Insert into database
                cursor.execute("""
                INSERT INTO disciplinary_cases 
                (case_id, case_type, case_status, sheet_origin, scope, cpf_no, 
                 employee_name, dc_number, facts_of_case, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    case_id,
                    case_type,
                    "active" if "close" not in case_type else "closed",
                    sheet_name,
                    meta.get("scope", "statewise"),
                    cpf,
                    safe_text(row.iloc[0]) if len(row) > 0 else "",  # Name from first column
                    dc_number,
                    facts,
                    "migration_script"
                ))
                
                total_migrated += 1
                
            except Exception as e:
                print(f"Error migrating row {row_idx} in {sheet_name}: {e}")
    
    conn.commit()
    conn.close()
    print(f"Migrated {total_migrated} disciplinary cases to database")

if __name__ == "__main__":
    migrate_cases()
```

### Step 3.3: Run Migration Scripts
```bash
# Migrate employees first
python migrate_employees.py

# Then migrate cases
python migrate_cases.py
```

### Step 3.4: Verify Migration
Create file: `verify_migration.py`

```python
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

def verify_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count employees
    cursor.execute("SELECT COUNT(*) FROM employees")
    emp_count = cursor.fetchone()[0]
    
    # Count cases by type
    cursor.execute("SELECT case_type, COUNT(*) FROM disciplinary_cases GROUP BY case_type")
    case_counts = cursor.fetchall()
    
    # Count by sheet
    cursor.execute("SELECT sheet_origin, COUNT(*) FROM disciplinary_cases GROUP BY sheet_origin")
    sheet_counts = cursor.fetchall()
    
    print(f"Employees migrated: {emp_count}")
    print("\nCases by type:")
    for case_type, count in case_counts:
        print(f"  {case_type}: {count}")
    
    print("\nCases by sheet:")
    for sheet, count in sheet_counts:
        print(f"  {sheet}: {count}")
    
    conn.close()

if __name__ == "__main__":
    verify_migration()
```

```bash
python verify_migration.py
```

---

## PHASE 4: Application Code Updates

### Step 4.1: Create Database Manager Module
Create file: `DC_DatabaseManager.py`

```python
import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_employee_by_cpf(self, cpf):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE cpf_no = ?", (cpf,))
            return dict(cursor.fetchone()) if cursor.fetchone() else None
    
    def get_cases_by_sheet(self, sheet_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM disciplinary_cases 
                WHERE sheet_origin = ? 
                ORDER BY created_at DESC
            """, (sheet_name,))
            return [dict(row) for row in cursor.fetchall()]
    
    def insert_case(self, case_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disciplinary_cases 
                (case_id, case_type, case_status, sheet_origin, scope, cpf_no, 
                 employee_name, designation, present_office, facts_of_case, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_data.get('case_id'),
                case_data.get('case_type'),
                case_data.get('case_status', 'active'),
                case_data.get('sheet_origin'),
                case_data.get('scope'),
                case_data.get('cpf_no'),
                case_data.get('employee_name'),
                case_data.get('designation'),
                case_data.get('present_office'),
                case_data.get('facts_of_case'),
                case_data.get('created_by', 'system')
            ))
            return cursor.lastrowid
    
    def update_case(self, case_id, update_data, updated_by):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get old values for audit trail
            cursor.execute("SELECT * FROM disciplinary_cases WHERE id = ?", (case_id,))
            old_case = dict(cursor.fetchone())
            
            # Build update query
            update_fields = []
            update_values = []
            for field, value in update_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            update_values.append(updated_by)
            update_values.append(datetime.now().isoformat())
            update_values.append(case_id)
            
            cursor.execute(f"""
                UPDATE disciplinary_cases 
                SET {', '.join(update_fields)}, updated_by = ?, updated_at = ?
                WHERE id = ?
            """, update_values)
            
            # Add to audit trail
            cursor.execute("""
                INSERT INTO case_history 
                (case_id, action_type, old_values, new_values, changed_by, notes)
                VALUES (?, 'updated', ?, ?, ?, ?)
            """, (case_id, json.dumps(old_case), json.dumps(update_data), updated_by, 'Case updated'))
            
            return cursor.rowcount > 0

# Create global instance
db_manager = DatabaseManager()
```

### Step 4.2: Update DC_DataLoader to Use Database
Modify `DC_DataLoader.py`:

```python
# Add at top of file
from DC_DatabaseManager import db_manager

# Add new method to DCDataLoader class
def load_cases_from_database(self, sheet_name):
    """Load cases from database instead of Excel"""
    return db_manager.get_cases_by_sheet(sheet_name)

# Modify existing load_dc_sheet method to check database first
def load_dc_sheet(self, sheet_name, use_cache=True):
    # Try database first
    try:
        cases = self.load_cases_from_database(sheet_name)
        if cases:
            return pd.DataFrame(cases)
    except Exception:
        pass
    
    # Fallback to Excel if database fails
    # ... existing Excel loading code ...
```

### Step 4.3: Update DC_Editor to Save to Database
Modify `DC_Editor.py`:

```python
# Add database save method
def save_case_to_database(self, case_data):
    """Save case data to database"""
    from DC_DatabaseManager import db_manager
    
    case_id = case_data.get('case_id')
    if case_id:
        # Update existing case
        return db_manager.update_case(case_id, case_data, session.get('user_name', 'system'))
    else:
        # Insert new case
        return db_manager.insert_case(case_data)
```

---

## PHASE 5: Testing & Validation

### Step 5.1: Create Test Script
Create file: `test_database.py`

```python
import sqlite3
import os
from DC_DatabaseManager import db_manager

def test_database_operations():
    print("Testing database operations...")
    
    # Test employee lookup
    emp = db_manager.get_employee_by_cpf("2266083")
    print(f"Employee lookup: {'PASS' if emp else 'FAIL'}")
    
    # Test case retrieval
    cases = db_manager.get_cases_by_sheet("4DC")
    print(f"Case retrieval: {'PASS' if cases else 'FAIL'}")
    
    # Test case insertion
    test_case = {
        'case_id': f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'case_type': 'minor',
        'case_status': 'active',
        'sheet_origin': '4DC',
        'scope': 'statewise',
        'cpf_no': '2266083',
        'employee_name': 'Test Employee',
        'designation': 'Test Designation',
        'present_office': 'Test Office',
        'facts_of_case': 'Test case facts',
        'created_by': 'test_script'
    }
    
    case_id = db_manager.insert_case(test_case)
    print(f"Case insertion: {'PASS' if case_id else 'FAIL'}")
    
    print("Database tests completed")

if __name__ == "__main__":
    test_database_operations()
```

### Step 5.2: Run Tests
```bash
python test_database.py
```

---

## PHASE 6: Backup & Recovery

### Step 6.1: Create Backup Script
Create file: `backup_database.py`

```python
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
```

### Step 6.2: Create Restore Script
Create file: `restore_database.py`

```python
import sqlite3
import shutil
import os

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
```

---

## PHASE 7: Deployment

### Step 7.1: Update Dependencies
Add to `requirements.txt`:
```
sqlite3
sqlalchemy
```

### Step 7.2: Update Build Script
Modify `build_exe.bat` to include database files:
```batch
pyinstaller --noconfirm --onedir --windowed --add-data "templates;templates" --add-data "static;static" --add-data "runtime\database;runtime\database" --hidden-import "sqlite3" --name "DAMS" Run.py
```

### Step 7.3: Test Standalone Build
```bash
build_exe.bat
```

---

## TROUBLESHOOTING

### Issue: Database locked
**Solution:** Ensure only one connection at a time or use WAL mode
```python
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
```

### Issue: Migration fails
**Solution:** Check Excel file format and column mappings in META

### Issue: Performance slow
**Solution:** Add indexes on frequently queried columns
```python
cursor.execute("CREATE INDEX idx_cases_cpf ON disciplinary_cases(cpf_no)")
```

---

## VALIDATION CHECKLIST

- [ ] Database created successfully
- [ ] All employees migrated
- [ ] All cases migrated with correct types
- [ ] Sheet views configured
- [ ] Application loads data from database
- [ ] Application saves data to database
- [ ] Audit trail working
- [ ] Backup/restore functional
- [ ] Performance acceptable
- [ ] Mobile access working

---

## NEXT STEPS

After completing this implementation:
1. Monitor database performance
2. Gather user feedback
3. Optimize queries based on usage patterns
4. Consider PostgreSQL migration if concurrent users increase
5. Implement automated backup scheduling
