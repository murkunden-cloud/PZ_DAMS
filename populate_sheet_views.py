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
    {
        "sheet_name": "6DC",
        "display_name": "Minor DC - Consolidated (4DC+5DC)",
        "case_type_filter": "minor",
        "case_status_filter": "active",
        "scope_filter": "consolidated",
        "class_filter": "All",
        "sort_order": 3
    },
    {
        "sheet_name": "7DC",
        "display_name": "Minor Closed - Statewise",
        "case_type_filter": "minor_close",
        "case_status_filter": "closed",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 4
    },
    {
        "sheet_name": "8DC",
        "display_name": "Minor Closed - Circlewise",
        "case_type_filter": "minor_close",
        "case_status_filter": "closed",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 5
    },
    {
        "sheet_name": "12DC",
        "display_name": "Suspension - End of Last Month (Statewise)",
        "case_type_filter": "suspension",
        "case_status_filter": "active",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 6
    },
    {
        "sheet_name": "13DC",
        "display_name": "Suspension - End of Last Month (Circlewise)",
        "case_type_filter": "suspension",
        "case_status_filter": "active",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 7
    },
    {
        "sheet_name": "14DC",
        "display_name": "Suspension - Current Month (Statewise)",
        "case_type_filter": "suspension_current",
        "case_status_filter": "active",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 8
    },
    {
        "sheet_name": "15DC",
        "display_name": "Suspension - Current Month (Circlewise)",
        "case_type_filter": "suspension_current",
        "case_status_filter": "active",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 9
    },
    {
        "sheet_name": "16DC",
        "display_name": "Suspension Revoked - Statewise",
        "case_type_filter": "suspension_revoke",
        "case_status_filter": "revoked",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 10
    },
    {
        "sheet_name": "17DC",
        "display_name": "Suspension Revoked - Circlewise",
        "case_type_filter": "suspension_revoke",
        "case_status_filter": "revoked",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 11
    },
    {
        "sheet_name": "20DC",
        "display_name": "Major DC Chargesheet - Statewise",
        "case_type_filter": "major",
        "case_status_filter": "initiated",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 12
    },
    {
        "sheet_name": "21DC",
        "display_name": "Major DC Chargesheet - Circlewise",
        "case_type_filter": "major",
        "case_status_filter": "initiated",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 13
    },
    {
        "sheet_name": "22DC",
        "display_name": "Major DC All Cases - Statewise",
        "case_type_filter": "major_all",
        "case_status_filter": "active",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 14
    },
    {
        "sheet_name": "23DC",
        "display_name": "Major DC All Cases - Circlewise",
        "case_type_filter": "major_all",
        "case_status_filter": "active",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 15
    },
    {
        "sheet_name": "24DC",
        "display_name": "Major DC Finalised - Statewise",
        "case_type_filter": "major_finalised",
        "case_status_filter": "finalised",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 16
    },
    {
        "sheet_name": "25DC",
        "display_name": "Major DC Finalised - Circlewise",
        "case_type_filter": "major_finalised",
        "case_status_filter": "finalised",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 17
    },
    {
        "sheet_name": "29DC",
        "display_name": "Appeal Disposed - Statewise",
        "case_type_filter": "appeal",
        "case_status_filter": "closed",
        "scope_filter": "statewise",
        "class_filter": "All",
        "sort_order": 18
    },
    {
        "sheet_name": "30DC",
        "display_name": "Appeal Disposed - Circlewise",
        "case_type_filter": "appeal",
        "case_status_filter": "closed",
        "scope_filter": "circlewise",
        "class_filter": "All",
        "sort_order": 19
    },
    {
        "sheet_name": "32DC",
        "display_name": "Absconding Employees",
        "case_type_filter": "abstract",
        "case_status_filter": "active",
        "scope_filter": "all",
        "class_filter": "All",
        "sort_order": 20
    },
    {
        "sheet_name": "34DC",
        "display_name": "V&S Cases",
        "case_type_filter": "abstract",
        "case_status_filter": "active",
        "scope_filter": "all",
        "class_filter": "All",
        "sort_order": 21
    },
    {
        "sheet_name": "35DC",
        "display_name": "Man Handling Cases",
        "case_type_filter": "abstract",
        "case_status_filter": "active",
        "scope_filter": "all",
        "class_filter": "All",
        "sort_order": 22
    },
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
