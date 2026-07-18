import os
import re
from datetime import datetime

try:
    import pandas as pd
except ImportError as exc:
    raise RuntimeError("pandas is required. Install it with: pip install pandas openpyxl flask") from exc


import sys
import configparser

# Try to import database manager, but don't fail if not available
try:
    from DC_DatabaseManager import db_manager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Determine the actual application directory (handles PyInstaller)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

IS_VERCEL = os.environ.get("VERCEL") == "1"

if IS_VERCEL:
    RUNTIME_DIR = "/tmp/runtime"
else:
    RUNTIME_DIR = os.path.join(APP_DIR, "runtime")

BACKUP_DIR = os.path.join(RUNTIME_DIR, "backups")
CACHE_DIR = os.path.join(RUNTIME_DIR, "cache")
REPORT_DIR = os.path.join(RUNTIME_DIR, "reports")
CLOSED_DB = os.path.join(RUNTIME_DIR, "closed_cases_db.json")

for folder in (RUNTIME_DIR, BACKUP_DIR, CACHE_DIR, REPORT_DIR):
    os.makedirs(folder, exist_ok=True)


def resolve_data_file(*filenames):
    config_path = os.path.join(APP_DIR, 'config.ini')
    config_dir = ""
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        try:
            config.read(config_path)
            if 'Settings' in config and 'DataDirectory' in config['Settings']:
                config_dir = config['Settings']['DataDirectory'].strip()
        except Exception:
            pass

    env_root = os.environ.get("DC_MANAGER_DATA_DIR", "").strip()
    roots = [p for p in [config_dir, env_root, APP_DIR, os.path.dirname(APP_DIR), PROJECT_DIR] if p]
    
    for filename in filenames:
        for root in roots:
            candidate = os.path.join(root, filename)
            if os.path.exists(candidate):
                return candidate
                
    # fallback
    return os.path.join(roots[-1] if roots else APP_DIR, filenames[0] if filenames else "")


DC_FILE = resolve_data_file("origional_35_dc.xlsx", "35_dc.xlsx")
EMP_FILE = resolve_data_file("master_employe.xlsx", "master_employees.xlsx", "master_emp.xlsx")
EXTRACTED_DC_HEADER = "DC_NO_EXTRACTED"


META = {
    "4DC": {"type": "minor", "scope": "statewise", "title": "Minor DC - Statewise (Class I/II)", "cpf_col": 4, "dc_col": 10, "facts_col": 9, "data_start": 5},
    "5DC": {"type": "minor", "scope": "circlewise", "title": "Minor DC - Circlewise (Class III/IV)", "cpf_col": 4, "dc_col": 10, "facts_col": 9, "data_start": 5},
    "6DC": {"type": "minor", "scope": "consolidated", "title": "Minor DC - Consolidated (4DC+5DC)", "cpf_col": 4, "dc_col": 11, "dc_record_no_col": 19, "dc_record_date_col": 20, "facts_col": 10, "data_start": 4},
    "7DC": {"type": "minor_close", "scope": "statewise", "title": "Minor Closed - Statewise", "cpf_col": 4, "dc_col": 10, "facts_col": 9, "data_start": 4},
    "8DC": {"type": "minor_close", "scope": "circlewise", "title": "Minor Closed - Circlewise", "cpf_col": 3, "dc_col": 10, "facts_col": 9, "data_start": 5},
    "12DC": {"type": "suspension", "scope": "statewise", "title": "Suspension - End of Last Month (Statewise)", "cpf_col": 4, "dc_col": 9, "facts_col": 8, "data_start": 6},
    "13DC": {"type": "suspension", "scope": "circlewise", "title": "Suspension - End of Last Month (Circlewise)", "cpf_col": 3, "dc_col": 8, "facts_col": 7, "data_start": 5},
    "14DC": {"type": "suspension_current", "scope": "statewise", "title": "Suspension - Current Month (Statewise)", "cpf_col": 4, "dc_col": 9, "facts_col": 8, "data_start": 5, "actual_name": "14DC "},
    "15DC": {"type": "suspension_current", "scope": "circlewise", "title": "Suspension - Current Month (Circlewise)", "cpf_col": 3, "dc_col": 8, "facts_col": 7, "data_start": 5},
    "16DC": {"type": "suspension_revoke", "scope": "statewise", "title": "Suspension Revoked - Statewise", "cpf_col": 4, "dc_col": 8, "facts_col": 7, "data_start": 5, "actual_name": "16DC "},
    "17DC": {"type": "suspension_revoke", "scope": "circlewise", "title": "Suspension Revoked - Circlewise", "cpf_col": 3, "dc_col": 7, "facts_col": 6, "data_start": 5},
    "20DC": {"type": "major", "scope": "statewise", "title": "Major DC Chargesheet - Statewise", "cpf_col": 4, "dc_col": 10, "facts_col": 9, "data_start": 6},
    "21DC": {"type": "major", "scope": "circlewise", "title": "Major DC Chargesheet - Circlewise", "cpf_col": 4, "dc_col": 10, "facts_col": 9, "data_start": 5},
    "22DC": {"type": "major_all", "scope": "statewise", "title": "Major DC All Cases - Statewise", "cpf_col": 4, "dc_col": 10, "dc_record_no_col": 21, "dc_record_date_col": 22, "facts_col": 11, "data_start": 5},
    "23DC": {"type": "major_all", "scope": "circlewise", "title": "Major DC All Cases - Circlewise", "cpf_col": 4, "dc_col": 10, "dc_record_no_col": 21, "dc_record_date_col": 22, "facts_col": 11, "data_start": 5},
    "24DC": {"type": "major_finalised", "scope": "statewise", "title": "Major DC Finalised - Statewise", "cpf_col": 4, "dc_col": 10, "facts_col": 9, "data_start": 4},
    "25DC": {"type": "major_finalised", "scope": "circlewise", "title": "Major DC Finalised - Circlewise", "cpf_col": 3, "dc_col": 9, "facts_col": 8, "data_start": 6},
    "29DC": {"type": "appeal", "scope": "statewise", "title": "Appeal Disposed - Statewise", "cpf_col": 3, "dc_col": 7, "facts_col": 6, "data_start": 4},
    "30DC": {"type": "appeal", "scope": "circlewise", "title": "Appeal Disposed - Circlewise", "cpf_col": 3, "dc_col": 7, "facts_col": 6, "data_start": 5},
    "32DC": {"type": "abstract", "scope": "all", "title": "Absconding Employees"},
    "34DC": {"type": "abstract", "scope": "all", "title": "V&S Cases", "actual_name": "34DC "},
    "35DC": {"type": "abstract", "scope": "all", "title": "Man Handling Cases"},
}

OP_SHEETS = [sheet for sheet, meta in META.items() if meta.get("type") != "abstract"]

ACTIVE_CASE_SHEETS = {
    "minor": ["6DC"],
    "major": ["22DC", "23DC"],
}

DISPLAY_BADGES = {
    "minor": "minor",
    "minor_close": "minor",
    "major": "major",
    "major_all": "major",
    "major_finalised": "major",
    "suspension": "suspension",
    "suspension_current": "suspension",
    "suspension_revoke": "suspension_revoke",
    "appeal": "appeal",
}

DC_PATTERNS = [
    re.compile(r"/(\d+)\s*$"),
    re.compile(r"[Ll]etter\s*[Nn]o.*?(\d+)"),
    re.compile(r"/(\d{3,})/"),
    re.compile(r"(\d{3,6})\s*$"),
]

MASTER_EMPLOYEE_COLUMNS = [
    "CPFNO",
    "EmployeeName",
    "Designation",
    "PresentOffice",
    "presentDivision",
    "PresentCircle",
    "PresentZone",
    "Remarks",
    "brthdt",
    "dtofretir",
    "paygrp"
]


def normalize_cpf(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in ("", "nan", "none"):
        return ""
    if re.fullmatch(r"\d+(?:\.0+)?", text):
        text = text.split(".", 1)[0]
    digits = re.sub(r"\D+", "", text)
    if digits:
        return digits.lstrip("0") or "0"
    return ""  # If no digits found, it's not a valid CPF

def has_cpf_value(value):
    raw = str(value).strip().lower() if value is not None else ""
    norm = normalize_cpf(value)
    return bool(norm) and norm.isdigit()


def extract_dc(text):
    if not text or str(text).strip() in ("", "nan", "None"):
        return ""
    raw = str(text).strip()
    for pattern in DC_PATTERNS:
        match = pattern.search(raw)
        if match:
            number = match.group(1)
            try:
                if 1990 <= int(number) <= 2035:
                    continue
            except ValueError:
                pass
            return number
    numbers = re.findall(r"\d+", raw)
    return max(numbers, key=len) if numbers else raw[:20]


def safe_text(value):
    import pandas as pd
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in ("nan", "nat", "none"):
        return ""
        
    import re
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?: \d{2}:\d{2}:\d{2}(?:\.\d+)?)?", text)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        
    return text


def row_to_strings(row_values, limit=None):
    values = [safe_text(value) for value in row_values]
    return values[:limit] if limit else values


def build_empty_employee_df():
    frame = pd.DataFrame(columns=MASTER_EMPLOYEE_COLUMNS + ["CPFNO_NORM"])
    return frame


class DCDataLoader:
    def __init__(self):
        self.dc_file = DC_FILE
        self.emp_file = EMP_FILE
        self.cache_dir = CACHE_DIR
        self.meta = META
        self.op_sheets = OP_SHEETS
        self._emp_cache = None
        self._sheet_cache = {}
        self._last_dc_mtime = 0
        self._last_emp_mtime = 0

    def check_file_modifications(self):
        dc_mtime = os.path.getmtime(self.dc_file) if os.path.exists(self.dc_file) else 0
        emp_mtime = os.path.getmtime(self.emp_file) if os.path.exists(self.emp_file) else 0
        dc_size = os.path.getsize(self.dc_file) if os.path.exists(self.dc_file) else 0
        emp_size = os.path.getsize(self.emp_file) if os.path.exists(self.emp_file) else 0
        
        meta_file = os.path.join(self.cache_dir, "cache_meta.json")
        stored_dc_mtime = 0
        stored_dc_size = 0
        stored_emp_mtime = 0
        stored_emp_size = 0
        
        if os.path.exists(meta_file):
            try:
                import json
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    stored_dc_mtime = meta.get("dc_mtime", 0)
                    stored_dc_size = meta.get("dc_size", 0)
                    stored_emp_mtime = meta.get("emp_mtime", 0)
                    stored_emp_size = meta.get("emp_size", 0)
            except Exception:
                pass

        changed = False
        if dc_mtime != stored_dc_mtime or dc_size != stored_dc_size or emp_mtime != stored_emp_mtime or emp_size != stored_emp_size:
            changed = True
            
        if (self._last_dc_mtime != 0 and dc_mtime != self._last_dc_mtime) or \
           (self._last_emp_mtime != 0 and emp_mtime != self._last_emp_mtime):
            changed = True

        if changed:
            self.clear_cache()
            self._last_dc_mtime = dc_mtime
            self._last_emp_mtime = emp_mtime
            try:
                import json
                with open(meta_file, 'w') as f:
                    json.dump({
                        "dc_mtime": dc_mtime,
                        "dc_size": dc_size,
                        "emp_mtime": emp_mtime,
                        "emp_size": emp_size
                    }, f)
            except Exception:
                pass
        elif self._last_dc_mtime == 0 or self._last_emp_mtime == 0:
            self._last_dc_mtime = dc_mtime
            self._last_emp_mtime = emp_mtime

    def clear_cache(self):
        self._emp_cache = None
        self._sheet_cache.clear()
        for name in os.listdir(self.cache_dir):
            if name.endswith(".pkl"):
                try:
                    os.remove(os.path.join(self.cache_dir, name))
                except OSError:
                    pass

    def clear_sheet_cache(self, sheet_name):
        if sheet_name in self._sheet_cache:
            del self._sheet_cache[sheet_name]
        cache_file = os.path.join(self.cache_dir, f"dc_{sheet_name}.pkl")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except OSError:
                pass

    def get_sheet_meta(self, sheet_name):
        return self.meta.get(sheet_name, {})

    def load_emp(self, use_cache=True):
        self.check_file_modifications()
        if use_cache and self._emp_cache is not None:
            return self._emp_cache
            
        cache_file = os.path.join(self.cache_dir, "emp.pkl")
        if use_cache and os.path.exists(cache_file):
            try:
                self._emp_cache = pd.read_pickle(cache_file)
                return self._emp_cache
            except Exception:
                pass
                
        if not os.path.exists(self.emp_file):
            frame = build_empty_employee_df()
            frame.to_pickle(cache_file)
            self._emp_cache = frame
            return frame
            
        frame = pd.read_excel(self.emp_file, sheet_name=0, dtype={"CPFNO": str})
        for column in MASTER_EMPLOYEE_COLUMNS:
            if column not in frame.columns:
                frame[column] = ""
            else:
                # Convert potential Timestamps to strings before filling NA
                frame[column] = frame[column].astype(str).replace('NaT', '').replace('nan', '')
                
        frame["CPFNO"] = frame["CPFNO"].astype(str).str.strip()
        frame["CPFNO_NORM"] = frame["CPFNO"].apply(normalize_cpf)
        for column in MASTER_EMPLOYEE_COLUMNS:
            frame[column] = frame[column].fillna("")
        frame.to_pickle(cache_file)
        self._emp_cache = frame
        return frame

    def get_post_mapping(self):
        if hasattr(self, '_post_cache') and self._post_cache is not None:
            return self._post_cache
        
        post_file = os.path.join(os.path.dirname(self.dc_file), 'post.xlsx')
        if not os.path.exists(post_file):
            self._post_cache = {}
            return {}
            
        try:
            df = pd.read_excel(post_file)
            mapping = {}
            for _, row in df.iterrows():
                org_desig = str(row.get('Org_desigz', '')).strip().lower()
                mstr_desig = str(row.get('mstr_desigz', '')).strip().lower()
                seniority = str(row.get('seniority', '')).strip()
                paygrp = str(row.get('paygrp', '')).strip()
                
                val = {'seniority': seniority, 'paygrp': paygrp}
                if org_desig:
                    mapping[org_desig] = val
                if mstr_desig:
                    mapping[mstr_desig] = val
            self._post_cache = mapping
            return mapping
        except Exception as e:
            import traceback
            print(f"Error reading post.xlsx: {e}")
            traceback.print_exc()
            return {}

    def get_designation_seniority(self, designation):
        if not designation:
            return "Circle"
        mapping = self.get_post_mapping()
        val = mapping.get(str(designation).strip().lower())
        if val and isinstance(val, dict):
            return val.get('seniority', 'Circle')
        return "Circle"

    def get_designation_paygrp(self, designation):
        if not designation:
            return ""
        mapping = self.get_post_mapping()
        val = mapping.get(str(designation).strip().lower())
        if val and isinstance(val, dict):
            return val.get('paygrp', '')
        return ""

    def normalize_paygroup(self, pg_val):
        if not pg_val:
            return ""
        val = str(pg_val).strip().upper()
        if val in ("1", "1.0", "I"): return "I"
        if val in ("2", "2.0", "II"): return "II"
        if val in ("3", "3.0", "III"): return "III"
        if val in ("4", "4.0", "IV"): return "IV"
        return val

    def resolve_seniority(self, designation, paygroup):
        pg = self.normalize_paygroup(paygroup)
        if pg in ("I", "II"):
            return "State"
        elif pg == "IV":
            return "Circle"
        else: # III or other
            return self.get_designation_seniority(designation)

    def load_cases_from_database(self, sheet_name):
        """Load cases from database instead of Excel"""
        if not DATABASE_AVAILABLE:
            return None
        try:
            cases = db_manager.get_cases_by_sheet(sheet_name)
            df = pd.DataFrame(cases) if cases else pd.DataFrame()
            # Transform database columns to Excel-like format
            # Map database columns to Excel column positions based on META
            meta = self.meta.get(sheet_name, {})
            excel_frame = self._transform_db_to_excel_format(df, sheet_name, meta)
            return excel_frame
        except Exception as e:
            print(f"Error loading from database: {e}")
        return None
    
    def _transform_db_to_excel_format(self, db_df, sheet_name, meta):
        """Transform database DataFrame to Excel-like format with numeric columns"""
        num_cols = max(meta.get("cpf_col", 4), meta.get("dc_col", 10), meta.get("facts_col", 9)) + 15
        
        # Helper to format a single row
        def format_row(row):
            excel_row = [""] * num_cols
            
            # Reconstruct Full Name, Designation, and Office
            name_part = safe_text(row.get('employee_name', ''))
            desig_part = safe_text(row.get('designation', ''))
            office_part = safe_text(row.get('present_office', ''))
            
            # User requested only name in column 1
            excel_row[1] = name_part
            
            # Place Designation and Office in columns 2 and 3 if available
            excel_row[2] = desig_part
            excel_row[3] = office_part
            
            cpf_col = meta.get("cpf_col", 4) - 1
            if cpf_col >= 0 and cpf_col < num_cols:
                excel_row[cpf_col] = safe_text(row.get('cpf_no', ''))
                
            dc_col = meta.get("dc_col", 10) - 1
            if dc_col >= 0 and dc_col < num_cols:
                excel_row[dc_col] = safe_text(row.get('dc_number', ''))
                
            facts_col = meta.get("facts_col", 9) - 1
            if facts_col >= 0 and facts_col < num_cols:
                excel_row[facts_col] = safe_text(row.get('facts_of_case', ''))

            # Map the specific export columns based on sheet structure
            if sheet_name in ["6DC", "7DC", "8DC"]:
                if len(excel_row) > 20:
                    raw_pg = row.get('pay_group', '')
                    pg = self.normalize_paygroup(raw_pg) or self.get_designation_paygrp(desig_part) or "IV"
                    excel_row[4] = safe_text(pg)
                    dob = safe_text(row.get('birth_date', ''))
                    ret = safe_text(row.get('retirement_date', ''))
                    excel_row[5] = f"{dob}\n{ret}" if dob or ret else ""
                    excel_row[6] = office_part
                    
                    excel_row[8] = safe_text(row.get('export_type_of_case', ''))
                    excel_row[9] = safe_text(row.get('facts_of_case', ''))
                    excel_row[10] = safe_text(row.get('dc_number', ''))
                    excel_row[11] = safe_text(row.get('export_suspension_details', ''))
                    excel_row[12] = safe_text(row.get('export_present_status', ''))
                    excel_row[15] = safe_text(row.get('export_final_order', ''))
                    excel_row[16] = safe_text(row.get('export_outcome', ''))
                    excel_row[17] = safe_text(row.get('present_circle', ''))
                    excel_row[18] = safe_text(row.get('dc_record_number', ''))
                    excel_row[19] = safe_text(row.get('dc_record_date', ''))
                    excel_row[20] = safe_text(row.get('remarks', ''))

            elif sheet_name in ["22DC", "23DC", "20DC", "21DC", "24DC", "25DC"]:
                if len(excel_row) > 20:
                    raw_pg = row.get('pay_group', '')
                    pg = self.normalize_paygroup(raw_pg) or self.get_designation_paygrp(desig_part) or "IV"
                    excel_row[4] = safe_text(pg)
                    dob = safe_text(row.get('birth_date', ''))
                    ret = safe_text(row.get('retirement_date', ''))
                    excel_row[5] = f"{dob}\n{ret}" if dob or ret else ""
                    excel_row[6] = office_part
                    
                    excel_row[8] = safe_text(row.get('export_type_of_case', ''))
                    excel_row[9] = safe_text(row.get('facts_of_case', ''))
                    excel_row[10] = safe_text(row.get('dc_number', ''))
                    excel_row[11] = safe_text(row.get('export_suspension_details', ''))
                    excel_row[12] = safe_text(row.get('enquiry_officer', ''))
                    excel_row[13] = safe_text(row.get('report_received_date', ''))
                    excel_row[14] = safe_text(row.get('scn_issued_details', ''))
                    excel_row[15] = safe_text(row.get('export_final_order', ''))
                    excel_row[16] = safe_text(row.get('export_outcome', ''))
                    excel_row[17] = safe_text(row.get('present_circle', ''))
                    excel_row[18] = safe_text(row.get('dc_record_number', ''))
                    excel_row[19] = safe_text(row.get('dc_record_date', ''))
                    excel_row[20] = safe_text(row.get('remarks', ''))
            
            return excel_row

        excel_data = []
        start_row = max(meta.get("data_start", 5) - 1, 0)
        
        # If 6DC (Consolidated), bifurcate into State vs Circle
        if sheet_name == "6DC":
            state_cases = []
            circle_cases = []
            
            for _, row in db_df.iterrows():
                desig = safe_text(row.get('designation', ''))
                seniority = self.get_designation_seniority(desig)
                if seniority.lower() == "state":
                    state_cases.append(format_row(row))
                else:
                    circle_cases.append(format_row(row))
                    
            # Headers for State
            for _ in range(start_row):
                excel_data.append([""] * num_cols)
                
            excel_data.extend(state_cases)
            
            # Separator for Circle cases
            sep_row = [""] * num_cols
            sep_row[1] = "Circlewise Seniority"
            excel_data.append(sep_row)
            
            excel_data.extend(circle_cases)
            
        else:
            # Default padding
            for _ in range(start_row):
                excel_data.append([""] * num_cols)
                
            for _, row in db_df.iterrows():
                excel_data.append(format_row(row))
        
        
        excel_frame = pd.DataFrame(excel_data)
        return excel_frame
    
    def load_dc_sheet(self, sheet_name, use_cache=True, filepath=None):
        self.check_file_modifications()
        
        # Try database first if available
        if filepath is None and DATABASE_AVAILABLE:
            try:
                db_frame = self.load_cases_from_database(sheet_name)
                if db_frame is not None:
                    return db_frame
            except Exception:
                pass
        
        jurisdiction = "All"
        try:
            from flask import session, has_request_context
            if has_request_context():
                jurisdiction = session.get("user_jurisdiction", "All")
        except Exception:
            pass
            
        cache_key = f"{sheet_name}_{jurisdiction.replace(' ', '_')}"
        
        if filepath is None and use_cache and cache_key in self._sheet_cache:
            return self._sheet_cache[cache_key]
            
        cache_file = os.path.join(self.cache_dir, f"dc_{cache_key}.pkl")
        if filepath is None and use_cache and os.path.exists(cache_file):
            try:
                frame = pd.read_pickle(cache_file)
                self._sheet_cache[cache_key] = frame
                return frame
            except Exception:
                pass
                
        target_file = filepath if filepath else self.dc_file
        if sheet_name not in self.meta or not os.path.exists(target_file):
            return None
        meta = self.meta[sheet_name]
        actual_sheet = meta.get("actual_name", sheet_name)
        
        import tempfile
        import shutil
        temp_path = None
        try:
            # Copy to temp file to bypass Windows file locks (PermissionError if opened in Excel)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsm") as tmp:
                temp_path = tmp.name
            shutil.copy2(target_file, temp_path)
            frame = pd.read_excel(temp_path, sheet_name=actual_sheet, header=None, dtype=str)
        except Exception:
            return None
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
                    
        frame = frame.fillna("")
        
        # Apply Jurisdiction Filtering
        if jurisdiction != "All":
            cpf_col_idx = meta.get("cpf_col", 4) - 1
            if cpf_col_idx < frame.shape[1]:
                emp_df = self.load_emp(use_cache=True)
                if not emp_df.empty and "CPFNO_NORM" in emp_df.columns:
                    # Get set of all CPFs in this jurisdiction
                    # Need to check if PresentCircle exists
                    if "PresentCircle" in emp_df.columns:
                        valid_rows = emp_df[emp_df["PresentCircle"].astype(str).str.lower().str.contains(jurisdiction.lower(), na=False)]
                        valid_cpfs = set(valid_rows["CPFNO_NORM"].astype(str))
                        
                        def is_valid_cpf(val):
                            norm = str(val).strip().lstrip('0')
                            return (not norm) or (norm in valid_cpfs)
                            
                        # Filter dataframe (keep rows where CPF is empty or matches valid_cpfs)
                        # We also keep headers (first few rows usually don't match CPFs but we must not delete them)
                        # Let's use start_row from meta to only filter data rows
                        start_row = max(meta.get("data_start", 5) - 1, 0)
                        
                        mask = pd.Series(True, index=frame.index)
                        for idx, val in frame.iloc[start_row:, cpf_col_idx].items():
                            mask[idx] = is_valid_cpf(val)
                            
                        frame = frame[mask]
        
        if "dc_col" in meta:
            col_index = meta["dc_col"] - 1
            if col_index < frame.shape[1]:
                frame[EXTRACTED_DC_HEADER] = frame.iloc[:, col_index].apply(extract_dc)
        if filepath is None:
            try:
                frame.to_pickle(cache_file)
            except Exception:
                pass
            self._sheet_cache[cache_key] = frame
        return frame

    def load_sheets(self, sheet_list, use_cache=True, filepath=None):
        data = {}
        for sheet_name in sheet_list:
            frame = self.load_dc_sheet(sheet_name, use_cache=use_cache, filepath=filepath)
            if frame is not None:
                data[sheet_name] = frame
        return data

    def load_all(self, use_cache=True):
        data = {}
        for sheet_name in self.meta:
            frame = self.load_dc_sheet(sheet_name, use_cache=use_cache)
            if frame is not None:
                data[sheet_name] = frame
        return data

    def ensure_source_files(self):
        return {
            "dc_file": self.dc_file,
            "dc_exists": os.path.exists(self.dc_file),
            "emp_file": self.emp_file,
            "emp_exists": os.path.exists(self.emp_file),
            "checked_at": datetime.now().isoformat(),
        }
