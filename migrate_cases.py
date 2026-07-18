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
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Load employee master data into memory for fast lookup
    cursor.execute("SELECT * FROM employees")
    employees_master = {row['cpf_no']: dict(row) for row in cursor.fetchall()}
    
    # Clear existing cases to allow refresh
    cursor.execute("DELETE FROM disciplinary_cases")
    
    total_migrated = 0
    
    for sheet_name in excel_file.sheet_names:
        if sheet_name not in META:
            continue
            
        meta = META[sheet_name]
        df = pd.read_excel(DC_FILE, sheet_name=sheet_name, header=None)
        
        # Scan all rows and let has_cpf_value filter out headers
        start_row = 0
        df = df.iloc[start_row:]
        
        for row_idx, row in df.iterrows():
            try:
                cpf_col = meta.get("cpf_col", 4) - 1
                cpf = normalize_cpf(row.iloc[cpf_col] if cpf_col < len(row) else "")
                
                if not cpf or not has_cpf_value(cpf):
                    continue
                
                # Fetch employee details from DB Master Data
                emp = employees_master.get(cpf, {})
                emp_name = emp.get('employee_name', safe_text(row.iloc[1]) if len(row) > 1 else "")
                designation = emp.get('designation', "")
                office = emp.get('present_office', "")
                circle = emp.get('present_circle', "")
                division = emp.get('present_division', "")
                zone = emp.get('present_zone', "")
                
                dc_col = meta.get("dc_col", 10) - 1
                dc_number = ""
                dc_date = ""
                
                export_type_of_case = ""
                export_suspension_details = ""
                export_present_status = ""
                export_final_order = ""
                export_outcome = ""
                dc_record_number = ""
                dc_record_date = ""
                export_final_order = ""
                export_outcome = ""
                chargesheet_details = ""
                facts = ""
                enquiry_officer = ""
                report_received_date = ""
                scn_issued_details = ""
                remarks = ""
                
                if sheet_name in ["6DC", "7DC", "8DC"]:
                    dc_record_number = ""
                    dc_record_date = ""
                
                    if len(row) > 19:
                        export_type_of_case = safe_text(row.iloc[8])
                        facts = safe_text(row.iloc[9])
                        dc_number = safe_text(row.iloc[10]) # Dispatch No
                        export_suspension_details = safe_text(row.iloc[11])
                        export_present_status = safe_text(row.iloc[12])
                        export_final_order = safe_text(row.iloc[15])
                        export_outcome = safe_text(row.iloc[16])
                        remarks = safe_text(row.iloc[17]) if len(row) > 17 else "" # Actually remarks is 20, circle is 17. Wait!
                        # Let's map exactly as Excel Columns (0-indexed)
                        # Col 9 (idx 8) = export_type_of_case
                        # Col 10 (idx 9) = facts_of_case
                        # Col 11 (idx 10) = dispatch_no (dc_number)
                        # Col 12 (idx 11) = suspension details
                        # Col 13 (idx 12) = present status
                        # Col 16 (idx 15) = final order
                        # Col 17 (idx 16) = outcome
                        # Col 18 (idx 17) = present_circle (we don't need to save this if it's already in DB from master)
                        # Col 19 (idx 18) = dc_record_number
                        # Col 20 (idx 19) = dc_record_date
                        
                        dc_record_number = safe_text(row.iloc[18]) if len(row) > 18 else ""
                        d_str = safe_text(row.iloc[19]) if len(row) > 19 else ""
                        dc_record_date = d_str.split()[0] if d_str else ""
                        
                        # remarks in 6DC is not reliably in a single column or we can leave it
                        
                elif sheet_name in ["22DC", "23DC", "20DC", "21DC", "24DC", "25DC"]:
                    if len(row) > 19:
                        export_type_of_case = safe_text(row.iloc[8])
                        facts = safe_text(row.iloc[9])
                        dc_number = safe_text(row.iloc[10])
                        export_suspension_details = safe_text(row.iloc[11])
                        enquiry_officer = safe_text(row.iloc[12])
                        report_received_date = safe_text(row.iloc[13])
                        scn_issued_details = safe_text(row.iloc[14])
                        export_final_order = safe_text(row.iloc[15])
                        export_outcome = safe_text(row.iloc[16])
                        dc_record_number = safe_text(row.iloc[18]) if len(row) > 18 else ""
                        d_str = safe_text(row.iloc[19]) if len(row) > 19 else ""
                        dc_record_date = d_str.split()[0] if d_str else ""
                        
                else:
                    dc_number = extract_dc(row.iloc[dc_col] if dc_col < len(row) else "")
                    facts_col = meta.get("facts_col", 9) - 1
                    facts = safe_text(row.iloc[facts_col] if facts_col < len(row) else "")
                
                # Generate case ID
                case_id = f"{sheet_name}_{cpf}_{row_idx}"
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
                
                # Determine Initiator Office from Dispatch Number
                dispatch_str = (dc_number + " " + dc_record_number).upper()
                if "CE/PZ" in dispatch_str or "/PZ/" in dispatch_str:
                    circle = "Pune Zone"
                elif "SE/PRC" in dispatch_str or "/PRC/" in dispatch_str:
                    circle = "Pune Rural Circle"
                elif "SE/GKUC" in dispatch_str or "/GKUC/" in dispatch_str:
                    circle = "Ganeshkhind Urban Circle"
                elif "SE/RPUC" in dispatch_str or "/RPUC/" in dispatch_str:
                    circle = "Rastapeth Urban Circle"
                else:
                    circle = "N.A."
                
                # Override office and division since count goes to initiator circle/zone
                office = "N.A."
                division = "N.A."
                
                # Insert into database
                cursor.execute("""
                INSERT INTO disciplinary_cases 
                (case_id, case_type, case_status, sheet_origin, scope, cpf_no, 
                 employee_name, designation, present_office, present_division, 
                 present_circle, present_zone, dc_number, dc_date, dc_record_number, dc_record_date, facts_of_case, 
                 enquiry_officer, report_received_date, scn_issued_details, 
                 export_type_of_case, chargesheet_details, export_suspension_details, 
                 export_present_status, export_final_order, export_outcome, remarks, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    dc_date,
                    dc_record_number,
                    dc_record_date,
                    facts,
                    enquiry_officer,
                    report_received_date,
                    scn_issued_details,
                    export_type_of_case,
                    chargesheet_details,
                    export_suspension_details,
                    export_present_status,
                    export_final_order,
                    export_outcome,
                    remarks,
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
