import re
from collections import defaultdict
from datetime import datetime

from DC_DataLoader import ACTIVE_CASE_SHEETS, META, has_cpf_value, normalize_cpf, safe_text
from DC_Editor import split_dispatch_date

def parse_case_date(date_str):
    if not date_str:
        return None
    # normalize delimiters to dash
    normalized = re.sub(r'[./]', '-', date_str.strip())
    # try parsing dd-mm-yyyy or yyyy-mm-dd
    parts = normalized.split('-')
    if len(parts) == 3:
        try:
            if len(parts[0]) == 4:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
            else:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
            # normalize 2-digit years
            if year < 100:
                year += 2000 if year > 20 else 1900
            if 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
        except ValueError:
            pass
    return None


class DCPendencyEngine:
    def __init__(self, loader):
        self.loader = loader

    def calc_pendency(self, all_dc):
        sheet_counts = {}
        pend = {
            "minor": {"sw": 0, "cw": 0, "total": 0},
            "major": {"sw": 0, "cw": 0, "total": 0},
            "suspension": {"sw": 0, "cw": 0, "total": 0},
            "revoke": {"sw": 0, "cw": 0, "total": 0},
            "appeal": {"sw": 0, "cw": 0, "total": 0},
            "sheet": {},
            "as_of": datetime.now().strftime("%Y-%m-%d"),
        }
        for sheet_name, frame in all_dc.items():
            meta = META.get(sheet_name, {})
            if meta.get("type") == "abstract":
                continue
            cpf_index = meta.get("cpf_col", 3) - 1
            start_row = max(meta.get("data_start", 4) - 1, 0)
            count = 0
            for _, row in frame.iloc[start_row:].iterrows():
                cpf = row.iloc[cpf_index] if cpf_index < frame.shape[1] else ""
                if has_cpf_value(cpf):
                    count += 1
            pend["sheet"][sheet_name] = count
            sheet_counts[sheet_name] = count

        minor_6dc = all_dc.get("6DC")
        if minor_6dc is not None:
            sw, cw = self._count_6dc_sw_cw(minor_6dc)
            if sw + cw:
                pend["minor"]["sw"] = sw
                pend["minor"]["cw"] = cw
            else:
                pend["minor"]["sw"] = sheet_counts.get("4DC", 0)
                pend["minor"]["cw"] = sheet_counts.get("5DC", 0)
        else:
            pend["minor"]["sw"] = sheet_counts.get("4DC", 0)
            pend["minor"]["cw"] = sheet_counts.get("5DC", 0)
        pend["minor"]["total"] = sheet_counts.get("6DC", pend["minor"]["sw"] + pend["minor"]["cw"])
        pend["major"]["sw"] = sheet_counts.get("22DC", 0)
        pend["major"]["cw"] = sheet_counts.get("23DC", 0)
        pend["major"]["total"] = pend["major"]["sw"] + pend["major"]["cw"]
        pend["suspension"]["sw"] = sheet_counts.get("12DC", 0)
        pend["suspension"]["cw"] = sheet_counts.get("13DC", 0)
        pend["suspension"]["total"] = pend["suspension"]["sw"] + pend["suspension"]["cw"]
        pend["revoke"]["sw"] = sheet_counts.get("16DC", 0)
        pend["revoke"]["cw"] = sheet_counts.get("17DC", 0)
        pend["revoke"]["total"] = pend["revoke"]["sw"] + pend["revoke"]["cw"]
        pend["appeal"]["sw"] = sheet_counts.get("29DC", 0)
        pend["appeal"]["cw"] = sheet_counts.get("30DC", 0)
        pend["appeal"]["total"] = pend["appeal"]["sw"] + pend["appeal"]["cw"]
        return pend

    def build_org_summary(self, all_dc, employees):
        # We only need circle/initiator office counts for Minor, Major, Suspension
        counts = {}

        # Minor = 6DC, Major = 22DC/23DC, Suspension = 12DC/13DC
        active_sheets_map = {
            "minor": ["6DC"],
            "major": ["22DC", "23DC"],
            "suspension": ["12DC", "13DC"]
        }
        
        for category, sheets in active_sheets_map.items():
            for sheet_name in sheets:
                frame = all_dc.get(sheet_name)
                if frame is None or frame.empty:
                    continue
                meta = META.get(sheet_name, {})
                cpf_index = meta.get("cpf_col", 4) - 1
                dc_col_idx = meta.get("dc_col", 10) - 1
                start_row = max(meta.get("data_start", 4) - 1, 0)
                
                for idx, row in frame.iloc[start_row:].iterrows():
                    cpf = normalize_cpf(row.iloc[cpf_index] if cpf_index < frame.shape[1] else "")
                    if not has_cpf_value(cpf):
                        continue
                    
                    initiator_circle = "N.A."
                    for val in reversed(row.tolist()):
                        text = str(val).upper().strip()
                        if not text: continue
                        if 'RPUC' in text or 'RASTAPETH' in text or 'RASTA PETH' in text:
                            initiator_circle = "Rastapeth Urban Circle"
                            break
                        elif 'GKUC' in text or 'GANESHKHIND' in text:
                            initiator_circle = "Ganeshkhind Urban Circle"
                            break
                        elif 'PRC' in text or 'PUNE RURAL' in text:
                            initiator_circle = "Pune Rural Circle"
                            break
                        elif 'PZ' in text or 'PUNE ZONE' in text:
                            initiator_circle = "Pune Zone"
                            break
                    
                    if initiator_circle == "N.A.":
                        dispatch_val = str(row.iloc[dc_col_idx]).upper() if dc_col_idx < frame.shape[1] else ""
                        if 'RPUC' in dispatch_val or 'RASTAPETH' in dispatch_val or 'RASTA PETH' in dispatch_val:
                            initiator_circle = "Rastapeth Urban Circle"
                        elif 'GKUC' in dispatch_val or 'GANESHKHIND' in dispatch_val:
                            initiator_circle = "Ganeshkhind Urban Circle"
                        elif 'PRC' in dispatch_val or 'PUNE RURAL' in dispatch_val:
                            initiator_circle = "Pune Rural Circle"
                        elif 'PZ' in dispatch_val or 'PUNE ZONE' in dispatch_val:
                            initiator_circle = "Pune Zone"
                        else:
                            initiator_circle = "Other / Unknown Initiator"
                            
                    if initiator_circle not in counts:
                        counts[initiator_circle] = {"minor": 0, "major": 0, "suspension": 0, "total": 0}
                        
                    counts[initiator_circle][category] += 1
                    if category != "suspension":
                        counts[initiator_circle]["total"] += 1
                    
        # Format the output list
        circle_list = []
        for name, data in counts.items():
            data["name"] = name
            circle_list.append(data)
            
        def sort_key(x):
            if "Unknown" in x["name"] or "Other" in x["name"]:
                return "zzzzzz"
            return x["name"].lower()
            
        circle_list.sort(key=sort_key)
        
        return {
            "circle": circle_list
        }

    def _count_6dc_sw_cw(self, frame):
        if frame is None or frame.empty:
            return 0, 0
        meta = META.get("6DC", {})
        cpf_index = meta.get("cpf_col", 4) - 1
        pg_index = 4  # Pay Group is at index 4 for 6DC
        sw = 0
        cw = 0
        for _, row in frame.iterrows():
            cpf = row.iloc[cpf_index] if cpf_index < frame.shape[1] else None
            if not has_cpf_value(cpf):
                continue
            
            pg = str(row.iloc[pg_index]).strip().upper() if pg_index < frame.shape[1] else ""
            if pg in ['I', 'II', '1', '2']:
                sw += 1
            elif pg in ['III', 'IV', '3', '4']:
                cw += 1
            else:
                sw += 1
                
        return sw, cw

    def _sorted_summary(self, mapping):
        return [
            {"name": key, "count": value}
            for key, value in sorted(mapping.items(), key=lambda item: (-item[1], item[0]))
        ]

    def calc_date_pendency(self, all_dc):
        active_sheets = ["6DC", "22DC", "23DC"]
        year_counts = defaultdict(int)
        month_counts = defaultdict(int)
        unknown_count = 0
        
        for sheet_name in active_sheets:
            frame = all_dc.get(sheet_name)
            if frame is None or frame.empty:
                continue
            meta = META.get(sheet_name, {})
            cpf_col_idx = meta.get("cpf_col", 3) - 1
            dc_col_idx = meta.get("dc_col", 10) - 1
            start_row = max(meta.get("data_start", 4) - 1, 0)
            
            for idx, row in frame.iloc[start_row:].iterrows():
                cpf = row.iloc[cpf_col_idx] if cpf_col_idx < frame.shape[1] else ""
                if not has_cpf_value(cpf):
                    continue
                
                dispatch_val = row.iloc[dc_col_idx] if dc_col_idx < frame.shape[1] else ""
                _, date_str = split_dispatch_date(safe_text(dispatch_val))
                dt = parse_case_date(date_str)
                if dt:
                    year_counts[dt.year] += 1
                    month_counts[(dt.year, dt.month)] += 1
                else:
                    unknown_count += 1
                    
        yearly = []
        for y in sorted(year_counts.keys(), reverse=True):
            yearly.append({"year": y, "count": year_counts[y]})
            
        monthly = []
        for (y, m) in sorted(month_counts.keys(), key=lambda x: (-x[0], -x[1])):
            month_name = datetime(y, m, 1).strftime("%b %Y")
            monthly.append({
                "year": y,
                "month": m,
                "month_name": month_name,
                "count": month_counts[(y, m)]
            })
            
        return {
            "yearly": yearly,
            "monthly": monthly,
            "unknown": unknown_count
        }

    def build_agewise_org_summary(self, all_dc, employees, ref_date=None, category_filter=None):
        if not ref_date:
            ref_date = datetime.now()
            
        employee_lookup = {}
        if not employees.empty:
            for _, row in employees.iterrows():
                employee_lookup[row.get("CPFNO_NORM", "")] = safe_text(row.get("PayGroup", row.get("paygrp")))
                
        circle_summary = defaultdict(lambda: {"less_6m": 0, "six_to_twelve": 0, "one_to_two_yr": 0, "more_two_yr": 0, "unknown_date": 0, "total": 0})
        paygroup_summary = defaultdict(lambda: {"less_6m": 0, "six_to_twelve": 0, "one_to_two_yr": 0, "more_two_yr": 0, "unknown_date": 0, "total": 0})
        
        # Decide which sheets to process based on category_filter
        if category_filter == "minor":
            active_sheets = ACTIVE_CASE_SHEETS["minor"]
        elif category_filter == "major":
            active_sheets = ACTIVE_CASE_SHEETS["major"]
        elif category_filter == "suspension":
            active_sheets = ACTIVE_CASE_SHEETS["suspension"]
        else:
            # All active sheets (excluding suspension to avoid double counting, since they are part of major)
            active_sheets = []
            for cat in ("minor", "major"):
                for s in ACTIVE_CASE_SHEETS[cat]:
                    if s not in active_sheets:
                        active_sheets.append(s)
                        
        for sheet_name in active_sheets:
            frame = all_dc.get(sheet_name)
            if frame is None or frame.empty:
                continue
            meta = META.get(sheet_name, {})
            cpf_col_idx = meta.get("cpf_col", 3) - 1
            dc_col_idx = meta.get("dc_col", 10) - 1
            start_row = max(meta.get("data_start", 4) - 1, 0)
            
            for idx, row in frame.iloc[start_row:].iterrows():
                cpf = normalize_cpf(row.iloc[cpf_col_idx] if cpf_col_idx < frame.shape[1] else "")
                if not has_cpf_value(cpf):
                    continue
                
                initiator_circle = "N.A."
                for val in reversed(row.tolist()):
                    text = str(val).upper().strip()
                    if not text: continue
                    if 'RPUC' in text or 'RASTAPETH' in text or 'RASTA PETH' in text:
                        initiator_circle = "Rastapeth Urban Circle"
                        break
                    elif 'GKUC' in text or 'GANESHKHIND' in text:
                        initiator_circle = "Ganeshkhind Urban Circle"
                        break
                    elif 'PRC' in text or 'PUNE RURAL' in text:
                        initiator_circle = "Pune Rural Circle"
                        break
                    elif 'PZ' in text or 'PUNE ZONE' in text:
                        initiator_circle = "Pune Zone"
                        break
                
                if initiator_circle == "N.A.":
                    dispatch_val = str(row.iloc[dc_col_idx]).upper() if dc_col_idx < frame.shape[1] else ""
                    if 'RPUC' in dispatch_val or 'RASTAPETH' in dispatch_val or 'RASTA PETH' in dispatch_val:
                        initiator_circle = "Rastapeth Urban Circle"
                    elif 'GKUC' in dispatch_val or 'GANESHKHIND' in dispatch_val:
                        initiator_circle = "Ganeshkhind Urban Circle"
                    elif 'PRC' in dispatch_val or 'PUNE RURAL' in dispatch_val:
                        initiator_circle = "Pune Rural Circle"
                    elif 'PZ' in dispatch_val or 'PUNE ZONE' in dispatch_val:
                        initiator_circle = "Pune Zone"
                    else:
                        initiator_circle = "Other / Unknown Initiator"
                        
                pg_raw = employee_lookup.get(cpf)
                if not pg_raw or pg_raw == "Unknown":
                    if frame.shape[1] > 4:
                        fallback_pg = str(row.iloc[4]).strip()
                        if fallback_pg and fallback_pg.lower() not in ("nan", "none", "unknown"):
                            pg_raw = fallback_pg
                
                if pg_raw in ("1", 1.0, "I", "1.0", 1): pg = "Pay Group I"
                elif pg_raw in ("2", 2.0, "II", "2.0", 2): pg = "Pay Group II"
                elif pg_raw in ("3", 3.0, "III", "3.0", 3): 
                    is_state = False
                    if sheet_name in ("22DC", "12DC", "4DC"):
                        is_state = True
                    elif sheet_name not in ("23DC", "13DC", "5DC"):
                        if frame.shape[1] > 4:
                            col4 = str(row.iloc[4]).upper().strip()
                            if "-S" in col4 or "STATE" in col4:
                                is_state = True
                    pg = "Pay Group III (State)" if is_state else "Pay Group III (Circle)"
                elif pg_raw in ("4", 4.0, "IV", "4.0", 4): pg = "Pay Group IV"
                else: pg = "Unknown"
                
                dispatch_val_str = safe_text(row.iloc[dc_col_idx]) if dc_col_idx < frame.shape[1] else ""
                _, date_str = split_dispatch_date(dispatch_val_str)
                dt = parse_case_date(date_str)
                
                category = "unknown_date"
                if dt:
                    diff_days = (ref_date - dt).days
                    if diff_days < 183:
                        category = "less_6m"
                    elif diff_days < 365:
                        category = "six_to_twelve"
                    elif diff_days < 730:
                        category = "one_to_two_yr"
                    else:
                        category = "more_two_yr"
                        
                circle_summary[initiator_circle][category] += 1
                circle_summary[initiator_circle]["total"] += 1
                
                paygroup_summary[pg][category] += 1
                paygroup_summary[pg]["total"] += 1
                
        def sort_key(name):
            if "Unknown" in name or "Other" in name:
                return "zzzzzz"
            return name.lower()
            
        circle_list = []
        for name, counts in circle_summary.items():
            counts["name"] = name
            circle_list.append(counts)
        circle_list.sort(key=lambda x: sort_key(x["name"]))
        
        pg_list = []
        for name, counts in paygroup_summary.items():
            counts["name"] = name
            pg_list.append(counts)
        pg_list.sort(key=lambda x: sort_key(x["name"]))
            
        return {
            "circle": circle_list,
            "paygroup": pg_list
        }

    def build_paygroup_month_summary(self, all_dc, employees, category_filter=None):
        employee_lookup = {}
        if not employees.empty:
            for _, row in employees.iterrows():
                employee_lookup[row.get("CPFNO_NORM", "")] = safe_text(row.get("PayGroup", row.get("paygrp")))
        
        summary = {}
        active_sheets = []
        if category_filter == "minor":
            cats = ("minor",)
        elif category_filter == "major":
            cats = ("major",)
        elif category_filter == "suspension":
            cats = ("suspension",)
        else:
            cats = ("minor", "major") # Exclude suspension to avoid double counting
            
        for category in cats:
            for sheet_name in ACTIVE_CASE_SHEETS[category]:
                if sheet_name in all_dc and sheet_name not in active_sheets:
                    active_sheets.append(sheet_name)
                    
        import pandas as pd
        for sheet_name in active_sheets:
            frame = all_dc[sheet_name]
            meta = META[sheet_name]
            cpf_index = meta["cpf_col"] - 1
            date_col_idx = meta.get("dc_record_date_col", meta.get("dc_col", 10) + 1) - 1
            
            for _, row in frame.iterrows():
                cpf = normalize_cpf(row.iloc[cpf_index] if cpf_index < frame.shape[1] else "")
                if not has_cpf_value(cpf):
                    continue
                
                pg = employee_lookup.get(cpf) or "Unknown"
                
                date_val = row.iloc[date_col_idx] if date_col_idx < frame.shape[1] else None
                month_str = "Unknown"
                if pd.notna(date_val):
                    try:
                        if isinstance(date_val, pd.Timestamp):
                            month_str = date_val.strftime("%b %Y")
                        else:
                            dt = pd.to_datetime(str(date_val), errors='coerce', dayfirst=True)
                            if pd.notna(dt):
                                month_str = dt.strftime("%b %Y")
                    except Exception:
                        pass
                
                initiator_circle = "N.A."
                for val in reversed(row.tolist()):
                    text = str(val).upper().strip()
                    if not text: continue
                    if 'RPUC' in text or 'RASTAPETH' in text or 'RASTA PETH' in text:
                        initiator_circle = "Rastapeth Urban Circle"
                        break
                    elif 'GKUC' in text or 'GANESHKHIND' in text:
                        initiator_circle = "Ganeshkhind Urban Circle"
                        break
                    elif 'PRC' in text or 'PUNE RURAL' in text:
                        initiator_circle = "Pune Rural Circle"
                        break
                    elif 'PZ' in text or 'PUNE ZONE' in text:
                        initiator_circle = "Pune Zone"
                        break
                
                if initiator_circle == "N.A.":
                    dispatch_val = str(row.iloc[meta.get("dc_col", 10) - 1]).upper() if meta.get("dc_col", 10) - 1 < frame.shape[1] else ""
                    if 'RPUC' in dispatch_val or 'RASTAPETH' in dispatch_val or 'RASTA PETH' in dispatch_val:
                        initiator_circle = "Rastapeth Urban Circle"
                    elif 'GKUC' in dispatch_val or 'GANESHKHIND' in dispatch_val:
                        initiator_circle = "Ganeshkhind Urban Circle"
                    elif 'PRC' in dispatch_val or 'PUNE RURAL' in dispatch_val:
                        initiator_circle = "Pune Rural Circle"
                    elif 'PZ' in dispatch_val or 'PUNE ZONE' in dispatch_val:
                        initiator_circle = "Pune Zone"
                    else:
                        initiator_circle = "Other / Unknown Initiator"
                
                if initiator_circle not in summary:
                    summary[initiator_circle] = {}
                if month_str not in summary[initiator_circle]:
                    summary[initiator_circle][month_str] = {"I": 0, "II": 0, "III (State)": 0, "III (Circle)": 0, "IV": 0, "Unknown": 0}
                
                pg = employee_lookup.get(cpf)
                if not pg or pg == "Unknown":
                    if frame.shape[1] > 4:
                        fallback_pg = str(row.iloc[4]).strip()
                        if fallback_pg and fallback_pg.lower() not in ("nan", "none", "unknown"):
                            pg = fallback_pg
                
                if pg in ("1", 1.0, "I", "1.0", 1): summary[initiator_circle][month_str]["I"] += 1
                elif pg in ("2", 2.0, "II", "2.0", 2): summary[initiator_circle][month_str]["II"] += 1
                elif pg in ("3", 3.0, "III", "3.0", 3): 
                    is_state = False
                    if sheet_name in ("22DC", "12DC", "4DC"):
                        is_state = True
                    elif sheet_name not in ("23DC", "13DC", "5DC"):
                        if frame.shape[1] > 4:
                            col4 = str(row.iloc[4]).upper().strip()
                            if "-S" in col4 or "STATE" in col4:
                                is_state = True
                    pg_str = "III (State)" if is_state else "III (Circle)"
                    summary[initiator_circle][month_str][pg_str] += 1
                elif pg in ("4", 4.0, "IV", "4.0", 4): summary[initiator_circle][month_str]["IV"] += 1
                else: summary[initiator_circle][month_str]["Unknown"] += 1
                
        result = {}
        for circle, month_data in summary.items():
            result[circle] = []
            for m, counts in month_data.items():
                result[circle].append({
                    "Month": m,
                    "PayGroup I": counts["I"],
                    "PayGroup II": counts["II"],
                    "PayGroup III (State)": counts["III (State)"],
                    "PayGroup III (Circle)": counts["III (Circle)"],
                    "PayGroup IV": counts["IV"],
                    "Unknown": counts["Unknown"],
                    "Total": counts["I"] + counts["II"] + counts["III (State)"] + counts["III (Circle)"] + counts["IV"] + counts["Unknown"]
                })
        return result
