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
