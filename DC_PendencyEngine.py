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
        pend["suspension"]["sw"] = sheet_counts.get("14DC", 0) or sheet_counts.get("12DC", 0)
        pend["suspension"]["cw"] = sheet_counts.get("15DC", 0) or sheet_counts.get("13DC", 0)
        pend["suspension"]["total"] = pend["suspension"]["sw"] + pend["suspension"]["cw"]
        pend["revoke"]["sw"] = sheet_counts.get("16DC", 0)
        pend["revoke"]["cw"] = sheet_counts.get("17DC", 0)
        pend["revoke"]["total"] = pend["revoke"]["sw"] + pend["revoke"]["cw"]
        pend["appeal"]["sw"] = sheet_counts.get("29DC", 0)
        pend["appeal"]["cw"] = sheet_counts.get("30DC", 0)
        pend["appeal"]["total"] = pend["appeal"]["sw"] + pend["appeal"]["cw"]
        return pend

    def build_org_summary(self, all_dc, employees):
        employee_lookup = {}
        if not employees.empty:
            for _, row in employees.iterrows():
                employee_lookup[row.get("CPFNO_NORM", "")] = {
                    "zone": safe_text(row.get("PresentZone")),
                    "circle": safe_text(row.get("PresentCircle")),
                    "division": safe_text(row.get("presentDivision")),
                    "office": safe_text(row.get("PresentOffice")),
                }

        counts = {
            "zone": defaultdict(int),
            "circle": defaultdict(int),
            "division": defaultdict(int),
            "office": defaultdict(int),
        }

        active_sheets = []
        for category in ("minor", "major"):
            for sheet_name in ACTIVE_CASE_SHEETS[category]:
                if sheet_name in all_dc and sheet_name not in active_sheets:
                    active_sheets.append(sheet_name)

        for sheet_name in active_sheets:
            frame = all_dc[sheet_name]
            meta = META[sheet_name]
            cpf_index = meta["cpf_col"] - 1
            dc_col_idx = meta.get("dc_col", 10) - 1
            for _, row in frame.iterrows():
                cpf = normalize_cpf(row.iloc[cpf_index] if cpf_index < frame.shape[1] else "")
                if not has_cpf_value(cpf):
                    continue
                org = employee_lookup.get(cpf, {})
                dispatch_val = str(row.iloc[dc_col_idx]).strip().upper() if dc_col_idx < frame.shape[1] else ""
                is_zone_case = dispatch_val.startswith("CE/PZ")
                
                zone_name = org.get("zone") or "Unknown"
                
                if is_zone_case:
                    counts["zone"][zone_name] += 1
                    pseudo = f"{zone_name} Office"
                    counts["circle"][pseudo] += 1
                    counts["division"][pseudo] += 1
                    counts["office"][pseudo] += 1
                else:
                    counts["zone"][zone_name] += 1
                    counts["circle"][org.get("circle") or "Unknown"] += 1
                    counts["division"][org.get("division") or "Unknown"] += 1
                    counts["office"][org.get("office") or "Unknown"] += 1

        return {
            "zone": self._sorted_summary(counts["zone"]),
            "circle": self._sorted_summary(counts["circle"]),
            "division": self._sorted_summary(counts["division"]),
            "office": self._sorted_summary(counts["office"]),
        }

    def _count_6dc_sw_cw(self, frame):
        if frame is None or frame.empty:
            return 0, 0
        meta = META.get("6DC", {})
        cpf_index = meta.get("cpf_col", 3) - 1
        current = "sw"
        sw = 0
        cw = 0
        marker_columns = min(frame.shape[1], 8)
        for _, row in frame.iterrows():
            cpf = row.iloc[cpf_index] if cpf_index < frame.shape[1] else None
            if not has_cpf_value(cpf):
                continue
            for col_index in range(marker_columns):
                text = str(row.iloc[col_index]).strip().lower()
                if "circle wise" in text or "circlewise" in text:
                    current = "cw"
                    break
                if "statewise" in text or "state wise" in text:
                    current = "sw"
                    break
            if current == "sw":
                sw += 1
            elif current == "cw":
                cw += 1
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

    def build_agewise_org_summary(self, all_dc, employees, ref_date=None):
        if not ref_date:
            ref_date = datetime.now()
            
        employee_lookup = {}
        if not employees.empty:
            for _, row in employees.iterrows():
                employee_lookup[row.get("CPFNO_NORM", "")] = {
                    "circle": safe_text(row.get("PresentCircle")) or "Unknown",
                    "division": safe_text(row.get("presentDivision")) or "Unknown",
                    "office": safe_text(row.get("PresentOffice")) or "Unknown",
                }
                
        circle_summary = defaultdict(lambda: {"less_6m": 0, "six_to_twelve": 0, "one_to_two_yr": 0, "more_two_yr": 0, "unknown_date": 0, "total": 0})
        division_summary = defaultdict(lambda: {"less_6m": 0, "six_to_twelve": 0, "one_to_two_yr": 0, "more_two_yr": 0, "unknown_date": 0, "total": 0})
        office_summary = defaultdict(lambda: {"less_6m": 0, "six_to_twelve": 0, "one_to_two_yr": 0, "more_two_yr": 0, "unknown_date": 0, "total": 0})
        
        active_sheets = ["6DC", "22DC", "23DC"]
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
                
                dispatch_val = row.iloc[dc_col_idx] if dc_col_idx < frame.shape[1] else ""
                is_zone_case = str(dispatch_val).strip().upper().startswith("CE/PZ")
                
                org = employee_lookup.get(cpf, {"circle": "Unknown", "division": "Unknown", "office": "Unknown", "zone": "Unknown"})
                
                if is_zone_case:
                    zone_name = org.get("zone") or "Pune Zone"
                    pseudo = f"{zone_name} Office"
                    circle = pseudo
                    division = pseudo
                    office = pseudo
                else:
                    circle = org.get("circle") or "Unknown"
                    division = org.get("division") or "Unknown"
                    office = org.get("office") or "Unknown"
                
                _, date_str = split_dispatch_date(safe_text(dispatch_val))
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
                        
                circle_summary[circle][category] += 1
                circle_summary[circle]["total"] += 1
                
                division_summary[division][category] += 1
                division_summary[division]["total"] += 1
                
                office_summary[office][category] += 1
                office_summary[office]["total"] += 1
                
        def sort_key(name):
            if name == "Unknown":
                return "zzzzzz"
            return name.lower()
            
        circle_list = []
        for name, counts in circle_summary.items():
            counts["name"] = name
            circle_list.append(counts)
        circle_list.sort(key=lambda x: sort_key(x["name"]))
        
        division_list = []
        for name, counts in division_summary.items():
            counts["name"] = name
            division_list.append(counts)
        division_list.sort(key=lambda x: sort_key(x["name"]))

        office_list = []
        for name, counts in office_summary.items():
            counts["name"] = name
            office_list.append(counts)
        office_list.sort(key=lambda x: sort_key(x["name"]))
            
        return {
            "circle": circle_list,
            "division": division_list,
            "office": office_list
        }
