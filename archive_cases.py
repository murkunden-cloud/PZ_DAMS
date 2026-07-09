import sqlite3
import os
from datetime import datetime, timedelta
from DC_DatabaseManager import db_manager

DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

def archive_previous_month_closed_cases():
    """Archive closed cases from the previous month"""
    # Get previous month in YYYY-MM format
    today = datetime.now()
    if today.month == 1:
        prev_month = today.replace(year=today.year - 1, month=12)
    else:
        prev_month = today.replace(month=today.month - 1)
    
    target_month = prev_month.strftime("%Y-%m")
    
    print(f"Archiving closed cases from {target_month}...")
    
    archived_count = db_manager.archive_closed_cases(target_month, archived_by='archive_script')
    
    print(f"Archived {archived_count} cases from {target_month}")
    return archived_count

def list_archived_months():
    """List all months that have archived cases"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT archive_month, COUNT(*) as count, 
               MIN(case_closure_date) as first_closure,
               MAX(case_closure_date) as last_closure
        FROM archived_cases 
        GROUP BY archive_month 
        ORDER BY archive_month DESC
    """)
    
    months = cursor.fetchall()
    conn.close()
    
    print("\nArchived cases by month:")
    print("Month\tCount\tFirst Closure\tLast Closure")
    print("-" * 60)
    for month in months:
        print(f"{month[0]}\t{month[1]}\t{month[2]}\t{month[3]}")
    
    return months

def search_archived_cases(search_term=None, cpf_no=None, employee_name=None):
    """Search archived cases"""
    results = db_manager.search_archived_cases(
        search_term=search_term,
        cpf_no=cpf_no,
        employee_name=employee_name,
        limit=20
    )
    
    print(f"\nFound {len(results)} archived cases:")
    print("-" * 100)
    for case in results:
        print(f"ID: {case['id']}, CPF: {case['cpf_no']}, Name: {case['employee_name']}, "
              f"Type: {case['case_type']}, Closure: {case['case_closure_date']}, "
              f"DC: {case['dc_number']}")
    
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "archive":
        archive_previous_month_closed_cases()
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        list_archived_months()
    elif len(sys.argv) > 1 and sys.argv[1] == "search":
        search_term = sys.argv[2] if len(sys.argv) > 2 else None
        search_archived_cases(search_term=search_term)
    else:
        print("Usage:")
        print("  python archive_cases.py archive    # Archive previous month closed cases")
        print("  python archive_cases.py list      # List archived months")
        print("  python archive_cases.py search <term>  # Search archived cases")
