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
