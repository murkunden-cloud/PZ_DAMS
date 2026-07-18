import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = DATABASE_URL and DATABASE_URL.startswith("postgres")

IS_VERCEL = os.environ.get("VERCEL") == "1"
if IS_VERCEL:
    DB_PATH = "/tmp/runtime/database/dams.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "runtime", "database", "dams.db")

class CursorWrapper:
    def __init__(self, cursor, is_postgres=False):
        self.cursor = cursor
        self.is_postgres = is_postgres
        
    def _convert_query(self, query):
        if self.is_postgres:
            return query.replace('?', '%s')
        return query
        
    def execute(self, query, params=None):
        converted = self._convert_query(query)
        if params:
            self.cursor.execute(converted, params)
        else:
            self.cursor.execute(converted)
            
    def fetchone(self):
        return self.cursor.fetchone()
        
    def fetchall(self):
        return self.cursor.fetchall()
        
    @property
    def rowcount(self):
        return self.cursor.rowcount
        
    @property
    def lastrowid(self):
        return self.cursor.lastrowid

class ConnWrapper:
    def __init__(self, conn, is_postgres):
        self.conn = conn
        self.is_postgres = is_postgres
        
    def cursor(self):
        if self.is_postgres:
            return CursorWrapper(self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor), True)
        else:
            return CursorWrapper(self.conn.cursor(), False)
            
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        self.conn.close()

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        
    @contextmanager
    def get_connection(self):
        if IS_POSTGRES and PSYCOPG2_AVAILABLE:
            conn = psycopg2.connect(DATABASE_URL)
            try:
                yield ConnWrapper(conn, True)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield ConnWrapper(conn, False)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    
    def get_employee_by_cpf(self, cpf):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE cpf_no = ?", (cpf,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_cases_by_sheet(self, sheet_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, e.birth_date, e.retirement_date, e.pay_group 
                FROM disciplinary_cases d
                LEFT JOIN employees e ON d.cpf_no = e.cpf_no
                WHERE d.sheet_origin = ? 
                ORDER BY d.created_at DESC
            """, (sheet_name,))
            return [dict(row) for row in cursor.fetchall()]
    
    def insert_case(self, case_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO disciplinary_cases 
                (case_id, case_type, case_status, sheet_origin, scope, cpf_no, 
                 employee_name, designation, present_office, facts_of_case, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                case_data.get('case_id'),
                case_data.get('case_type'),
                case_data.get('case_status', 'active'),
                case_data.get('sheet_origin'),
                case_data.get('scope'),
                case_data.get('cpf_no'),
                case_data.get('employee_name'),
                case_data.get('designation'),
                case_data.get('present_office'),
                case_data.get('facts_of_case'),
                case_data.get('created_by', 'system')
            )
            
            if IS_POSTGRES and PSYCOPG2_AVAILABLE:
                query += " RETURNING id"
                cursor.execute(query, params)
                row = cursor.fetchone()
                return row['id'] if row else None
            else:
                cursor.execute(query, params)
                return cursor.lastrowid
    
    def update_case(self, case_id, update_data, updated_by):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get old values for audit trail
            cursor.execute("SELECT * FROM disciplinary_cases WHERE id = ?", (case_id,))
            old_case = cursor.fetchone()
            if not old_case:
                return False
            
            old_case_dict = dict(old_case)
            
            # Build update query
            update_fields = []
            update_values = []
            for field, value in update_data.items():
                if field != 'id':
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if not update_fields:
                return False
            
            update_values.append(updated_by)
            update_values.append(datetime.now().isoformat())
            update_values.append(case_id)
            
            cursor.execute(f"""
                UPDATE disciplinary_cases 
                SET {', '.join(update_fields)}, updated_by = ?, updated_at = ?
                WHERE id = ?
            """, update_values)
            
            # Add to audit trail
            cursor.execute("""
                INSERT INTO case_history 
                (case_id, action_type, old_values, new_values, changed_by, notes)
                VALUES (?, 'updated', ?, ?, ?, ?)
            """, (case_id, json.dumps(old_case_dict), json.dumps(update_data), updated_by, 'Case updated'))
            
            return cursor.rowcount > 0
    
    def get_sheet_view_config(self, sheet_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sheet_views 
                WHERE sheet_name = ? AND is_active = 1
            """, (sheet_name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_sheet_views(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sheet_views 
                WHERE is_active = 1 
                ORDER BY sort_order
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def archive_closed_cases(self, target_month, archived_by='system'):
        """Archive closed cases from a specific month to archived_cases table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find closed cases from the target month
            cursor.execute("""
                SELECT * FROM disciplinary_cases 
                WHERE case_status IN ('closed', 'finalised', 'revoked')
                AND case_closure_date IS NOT NULL
                AND case_closure_date LIKE ?
            """, (target_month + '%',))
            
            cases_to_archive = cursor.fetchall()
            archived_count = 0
            
            for case in cases_to_archive:
                case_dict = dict(case)
                
                # Insert into archived_cases
                cursor.execute("""
                    INSERT INTO archived_cases 
                    (original_case_id, case_type, original_sheet_origin, original_scope,
                     cpf_no, employee_name, designation, present_office, present_division,
                     present_circle, present_zone, dc_number, dc_date, facts_of_case,
                     chargesheet_details, enquiry_officer, punishment_awarded, appeal_details,
                     suspension_start_date, suspension_end_date, suspension_reason,
                     case_closure_date, closure_reason, remarks, archived_by, archive_month)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    case_dict.get('case_id'),
                    case_dict.get('case_type'),
                    case_dict.get('sheet_origin'),
                    case_dict.get('scope'),
                    case_dict.get('cpf_no'),
                    case_dict.get('employee_name'),
                    case_dict.get('designation'),
                    case_dict.get('present_office'),
                    case_dict.get('present_division'),
                    case_dict.get('present_circle'),
                    case_dict.get('present_zone'),
                    case_dict.get('dc_number'),
                    case_dict.get('dc_date'),
                    case_dict.get('facts_of_case'),
                    case_dict.get('chargesheet_details'),
                    case_dict.get('enquiry_officer'),
                    case_dict.get('punishment_awarded'),
                    case_dict.get('appeal_details'),
                    case_dict.get('suspension_start_date'),
                    case_dict.get('suspension_end_date'),
                    case_dict.get('suspension_reason'),
                    case_dict.get('case_closure_date'),
                    case_dict.get('remarks'),
                    case_dict.get('remarks'),
                    archived_by,
                    target_month
                ))
                
                # Delete from disciplinary_cases
                cursor.execute("DELETE FROM disciplinary_cases WHERE id = ?", (case_dict['id'],))
                archived_count += 1
            
            return archived_count
    
    def search_archived_cases(self, search_term=None, cpf_no=None, employee_name=None, 
                             case_type=None, archive_month=None, limit=100):
        """Search archived cases by various criteria"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM archived_cases WHERE 1=1"
            params = []
            
            if search_term:
                query += " AND (cpf_no LIKE ? OR employee_name LIKE ? OR dc_number LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if cpf_no:
                query += " AND cpf_no = ?"
                params.append(cpf_no)
            
            if employee_name:
                query += " AND employee_name LIKE ?"
                params.append(f"%{employee_name}%")
            
            if case_type:
                query += " AND case_type = ?"
                params.append(case_type)
            
            if archive_month:
                query += " AND archive_month = ?"
                params.append(archive_month)
            
            query += " ORDER BY archived_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_archived_case_by_id(self, archived_id):
        """Get a specific archived case by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM archived_cases WHERE id = ?", (archived_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

# Create global instance
db_manager = DatabaseManager()
