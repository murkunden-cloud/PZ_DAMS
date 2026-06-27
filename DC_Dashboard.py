from datetime import datetime

from DC_DataLoader import DISPLAY_BADGES, META, extract_dc, safe_text


class DCDashboard:
    def __init__(self, loader, pendency_engine):
        self.loader = loader
        self.pendency_engine = pendency_engine

    def build_dashboard_data(self):
        employees = self.loader.load_emp()
        all_dc = self.loader.load_sheets(self.loader.op_sheets, use_cache=True)
        pend = self.pendency_engine.calc_pendency(all_dc)
        org_summary = self.pendency_engine.build_org_summary(all_dc, employees)
        date_pendency = self.pendency_engine.calc_date_pendency(all_dc)

        sheet_rows = []
        for sheet_name in sorted(pend["sheet"].keys()):
            meta = META.get(sheet_name, {})
            sheet_rows.append(
                {
                    "sheet": sheet_name,
                    "title": meta.get("title", ""),
                    "type": meta.get("type", ""),
                    "scope": meta.get("scope", ""),
                    "count": pend["sheet"][sheet_name],
                    "badge_class": DISPLAY_BADGES.get(meta.get("type", ""), "gray"),
                }
            )

        return {
            "generated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "employee_count": len(employees),
            "pendency": pend,
            "sheet_rows": sheet_rows,
            "org_summary": org_summary,
            "date_pendency": date_pendency,
        }

    def summarize_employee_cases(self, cases):
        output = []
        for case in cases:
            row_data = case.get("row_data", [])
            dc_index = META.get(case["sheet"], {}).get("dc_col", 10) - 1
            dc_raw = row_data[dc_index] if dc_index < len(row_data) else ""
            output.append(
                {
                    "sheet": case["sheet"],
                    "row_number": case["row_number"],
                    "dc_no": extract_dc(dc_raw),
                    "preview": row_data[:12],
                }
            )
        return output

    def build_svg_chart(self, items, width=420, row_height=34, color="#2471a3"):
        if not items:
            return ""
        max_value = max(item["count"] for item in items) or 1
        height = len(items) * row_height + 20
        rows = []
        for idx, item in enumerate(items[:8]):
            y = 20 + idx * row_height
            bar_width = 220 * item["count"] / max_value
            rows.append(
                f"<text x='0' y='{y}' font-size='12' fill='#1a3a5c'>{safe_text(item['name'])[:24]}</text>"
                f"<rect x='160' y='{y-10}' rx='4' ry='4' width='{bar_width:.2f}' height='14' fill='{color}' opacity='0.85'></rect>"
                f"<text x='{165 + bar_width:.2f}' y='{y+1}' font-size='12' fill='#333'>{item['count']}</text>"
            )
        return f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}'>{''.join(rows)}</svg>"
