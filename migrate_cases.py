import sqlite3
import pandas as pd
import os
from datetime import datetime
from DC_DataLoader import DC_FILE, META, normalize_cpf, extract_dc, safe_text, has_cpf_value

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
                # Extract CPF - use column name if available, otherwise use index
                cpf = ""
                if 'CPFNO' in row.index:
                    cpf = normalize_cpf(row.get('CPFNO', ''))
                else:
                    cpf_col = meta.get("cpf_col", 3)
                    cpf = normalize_cpf(row.iloc[cpf_col] if cpf_col < len(row) else "")
                
                if not cpf or not has_cpf_value(cpf):
                    continue
                
                # Extract employee name
                emp_name = ""
                if 'EmployeeName' in row.index:
                    emp_name = safe_text(row.get('EmployeeName', ''))
                else:
                    emp_name = safe_text(row.iloc[0]) if len(row) > 0 else ""
                
                # Extract designation
                designation = ""
                if 'Designation' in row.index:
                    designation = safe_text(row.get('Designation', ''))
                
                # Extract office
                office = ""
                if 'PresentOffice' in row.index:
                    office = safe_text(row.get('PresentOffice', ''))
                
                # Extract circle
                circle = ""
                if 'PresentCircle' in row.index:
                    circle = safe_text(row.get('PresentCircle', ''))
                
                # Extract division
                division = ""
                if 'presentDivision' in row.index:
                    division = safe_text(row.get('presentDivision', ''))
                
                # Extract zone
                zone = ""
                if 'PresentZone' in row.index:
                    zone = safe_text(row.get('PresentZone', ''))
                
                # Extract DC number
                dc_col = meta.get("dc_col", 10)
                dc_number = extract_dc(row.iloc[dc_col] if dc_col < len(row) else "")
                
                # Extract facts
                facts_col = meta.get("facts_col", 9)
                facts = safe_text(row.iloc[facts_col] if facts_col < len(row) else "")
                
                # Generate case ID (use row index to ensure uniqueness)
                case_id = f"{sheet_name}_{cpf}_{row_idx}"
                
                # Determine case type
                case_type = meta.get("type", "minor")
                
                # Determine case status
                case_status = "active"
                if "close" in case_type:
                    case_status = "closed"
                elif "finalised" in case_type:
                    case_status = "finalised"
                elif "revoke" in case_type:
                    case_status = "revoked"
                elif "initiated" in case_type:
                    case_status = "initiated"
                
                # Insert into database
                cursor.execute("""
                INSERT INTO disciplinary_cases 
                (case_id, case_type, case_status, sheet_origin, scope, cpf_no, 
                 employee_name, designation, present_office, present_division, 
                 present_circle, present_zone, dc_number, facts_of_case, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    case_id,
                    case_type,
                    case_status,
                    sheet_name,
                    meta.get("scope", "statewise"),
                    cpf,
                    emp_name,
                    designation,
                    office,
                    division,
                    circle,
                    zone,
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
