import os
from DC_DatabaseManager import db_manager, IS_POSTGRES

def create_database():
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Dialect specific syntax
        pk_type = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
        bool_true = "TRUE" if IS_POSTGRES else "1"
        
        # Create employees table
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS employees (
            id {pk_type},
            cpf_no VARCHAR(20) UNIQUE NOT NULL,
            employee_name VARCHAR(200) NOT NULL,
            designation VARCHAR(100),
            present_office VARCHAR(200),
            present_division VARCHAR(100),
            present_circle VARCHAR(100),
            present_zone VARCHAR(100),
            remarks TEXT,
            birth_date DATE,
            retirement_date DATE,
            pay_group VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create disciplinary_cases table
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS disciplinary_cases (
            id {pk_type},
            case_id VARCHAR(50) UNIQUE NOT NULL,
            case_type VARCHAR(20) NOT NULL CHECK(case_type IN ('minor', 'minor_close', 'major', 'major_all', 'major_finalised', 'suspension', 'suspension_current', 'suspension_revoke', 'appeal', 'abstract')),
            case_status VARCHAR(20) DEFAULT 'active' CHECK(case_status IN ('initiated', 'active', 'closed', 'finalised', 'revoked')),
            sheet_origin VARCHAR(10) NOT NULL,
            scope VARCHAR(20) CHECK(scope IN ('statewise', 'circlewise', 'consolidated', 'all')),
            employee_id INTEGER,
            cpf_no VARCHAR(20) NOT NULL,
            employee_name VARCHAR(200) NOT NULL,
            designation VARCHAR(100),
            present_office VARCHAR(200),
            present_division VARCHAR(100),
            present_circle VARCHAR(100),
            present_zone VARCHAR(100),
            dc_number VARCHAR(100),
            dc_date DATE,
            dc_record_number VARCHAR(100),
            dc_record_date DATE,
            facts_of_case TEXT,
            chargesheet_details TEXT,
            enquiry_officer VARCHAR(200),
            punishment_awarded TEXT,
            appeal_details TEXT,
            suspension_start_date DATE,
            suspension_end_date VARCHAR(100),
            suspension_reason TEXT,
            case_closure_date DATE,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(50),
            updated_by VARCHAR(50),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
        """)
        
        # Create case_history table for audit trail
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS case_history (
            id {pk_type},
            case_id INTEGER NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            old_values TEXT,
            new_values TEXT,
            changed_by VARCHAR(50),
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (case_id) REFERENCES disciplinary_cases(id)
        )
        """)
        
        # Create sheet_views table for virtual sheet configurations
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS sheet_views (
            id {pk_type},
            sheet_name VARCHAR(10) UNIQUE NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            case_type_filter VARCHAR(20),
            case_status_filter VARCHAR(20),
            scope_filter VARCHAR(20),
            class_filter VARCHAR(20),
            column_mapping TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT {bool_true}
        )
        """)
        
        # Create archived_cases table for storing closed cases from previous months
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS archived_cases (
            id {pk_type},
            original_case_id VARCHAR(50) NOT NULL,
            case_type VARCHAR(20) NOT NULL,
            original_sheet_origin VARCHAR(10) NOT NULL,
            original_scope VARCHAR(20),
            cpf_no VARCHAR(20) NOT NULL,
            employee_name VARCHAR(200) NOT NULL,
            designation VARCHAR(100),
            present_office VARCHAR(200),
            present_division VARCHAR(100),
            present_circle VARCHAR(100),
            present_zone VARCHAR(100),
            dc_number VARCHAR(100),
            dc_date DATE,
            facts_of_case TEXT,
            chargesheet_details TEXT,
            enquiry_officer VARCHAR(200),
            punishment_awarded TEXT,
            appeal_details TEXT,
            suspension_start_date DATE,
            suspension_end_date VARCHAR(100),
            suspension_reason TEXT,
            case_closure_date DATE NOT NULL,
            closure_reason TEXT,
            remarks TEXT,
            archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived_by VARCHAR(50),
            archive_month VARCHAR(7),
            FOREIGN KEY (cpf_no) REFERENCES employees(cpf_no)
        )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_cpf ON disciplinary_cases(cpf_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_type ON disciplinary_cases(case_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_status ON disciplinary_cases(case_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_sheet ON disciplinary_cases(sheet_origin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employees_cpf ON employees(cpf_no)")
        
        # Create indexes for archived_cases table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_archived_cpf ON archived_cases(cpf_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_archived_type ON archived_cases(case_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_archived_month ON archived_cases(archive_month)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_archived_closure_date ON archived_cases(case_closure_date)")
        
        print("Database schema created successfully using", "PostgreSQL" if IS_POSTGRES else "SQLite")

if __name__ == "__main__":
    create_database()
