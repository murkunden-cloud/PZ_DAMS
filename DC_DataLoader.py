import os
import re
from datetime import datetime

try:
    import pandas as pd
except ImportError as exc:
    raise RuntimeError("pandas is required. Install it with: pip install pandas openpyxl flask") from exc


import sys
import configparser

# Determine the actual application directory (handles PyInstaller)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
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
    "22DC": {"type": "major_all", "scope": "statewise", "title": "Major DC All Cases - Statewise", "cpf_col": 4, "dc_col": 10, "dc_record_no_col": 11, "dc_record_date_col": 12, "facts_col": 9, "data_start": 5},
    "23DC": {"type": "major_all", "scope": "circlewise", "title": "Major DC All Cases - Circlewise", "cpf_col": 4, "dc_col": 10, "dc_record_no_col": 11, "dc_record_date_col": 12, "facts_col": 9, "data_start": 5},
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
    return text.lower()


def has_cpf_value(value):
    raw = str(value).strip().lower() if value is not None else ""
    norm = normalize_cpf(value)
    return bool(norm) and raw not in ("cpfno", "sr. no.", "srl no.", "name", "3", "4")


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
    if value is None:
        return ""
    return str(value).strip()


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
        if os.path.exists(self.dc_file):
            mtime = os.path.getmtime(self.dc_file)
            if mtime > self._last_dc_mtime:
                self._sheet_cache.clear()
                for name in os.listdir(self.cache_dir):
                    if name.startswith("dc_") and name.endswith(".pkl"):
                        pkl_path = os.path.join(self.cache_dir, name)
                        try:
                            if os.path.getmtime(pkl_path) < mtime:
                                os.remove(pkl_path)
                        except OSError:
                            pass
                self._last_dc_mtime = mtime
            
        if os.path.exists(self.emp_file):
            mtime = os.path.getmtime(self.emp_file)
            if mtime > self._last_emp_mtime:
                self._emp_cache = None
                emp_pkl = os.path.join(self.cache_dir, "emp.pkl")
                if os.path.exists(emp_pkl):
                    try:
                        if os.path.getmtime(emp_pkl) < mtime:
                            os.remove(emp_pkl)
                    except OSError:
                        pass
                self._last_emp_mtime = mtime

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

    def load_dc_sheet(self, sheet_name, use_cache=True, filepath=None):
        self.check_file_modifications()
        
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
        try:
            frame = pd.read_excel(target_file, sheet_name=actual_sheet, header=None, dtype=str)
        except Exception:
            return None
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
