import sqlite3
import os
from DC_DatabaseManager import db_manager
from datetime import datetime

def test_database_operations():
    print("Testing database operations...")
    
    # Test employee lookup
    emp = db_manager.get_employee_by_cpf("2266083")
    print(f"Employee lookup: {'PASS' if emp else 'FAIL'}")
    
    # Test case retrieval
    cases = db_manager.get_cases_by_sheet("4DC")
    print(f"Case retrieval: {'PASS' if cases else 'FAIL'}")
    
    # Test case insertion
    test_case = {
        'case_id': f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'case_type': 'minor',
        'case_status': 'active',
        'sheet_origin': '4DC',
        'scope': 'statewise',
        'cpf_no': '2266083',
        'employee_name': 'Test Employee',
        'designation': 'Test Designation',
        'present_office': 'Test Office',
        'facts_of_case': 'Test case facts',
        'created_by': 'test_script'
    }
    
    case_id = db_manager.insert_case(test_case)
    print(f"Case insertion: {'PASS' if case_id else 'FAIL'}")
    
    # Test sheet view config
    sheet_config = db_manager.get_sheet_view_config("4DC")
    print(f"Sheet view config: {'PASS' if sheet_config else 'FAIL'}")
    
    print("Database tests completed")

if __name__ == "__main__":
    test_database_operations()
