import os
import re

APP_DIR = r"d:\MYPRO\DC\DC_Manager"
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")

# 1. Update templates with Edit/View logic
def replace_edit_button(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to replace ">✏️ Edit<" with ">{% if is_admin %}✏️ Edit{% else %}👁️ View{% endif %}<"
    content = content.replace(">✏️ Edit<", ">{% if is_admin %}✏️ Edit{% else %}👁️ View{% endif %}<")
    # For Open / Edit
    content = content.replace(">Open / Edit<", ">{% if is_admin %}Open / Edit{% else %}Open / View{% endif %}<")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for tpl in ["home_new.html", "cases_by_date.html", "search_cpf.html", "search_name.html", "org_cases.html", "sheet_view.html"]:
    replace_edit_button(os.path.join(TEMPLATES_DIR, tpl))

# 2. Update record_detail.html to hide save buttons
rd_path = os.path.join(TEMPLATES_DIR, "record_detail.html")
if os.path.exists(rd_path):
    with open(rd_path, 'r', encoding='utf-8') as f:
        rd_content = f.read()
    
    # Replace action-buttons div contents
    old_buttons = """<button type="submit" class="btn btn-primary" onclick="setSubmitAction('save')">💾 Save Changes (Update Row)</button>"""
    new_buttons = """{% if is_admin %}
                <button type="submit" class="btn btn-primary" onclick="setSubmitAction('save')">💾 Save Changes (Update Row)</button>
                {% else %}
                <div style="padding:10px; background:#f1f2f6; border-radius:5px; color:#7f8c8d; font-size:14px;">👁️ You are in View-Only mode. Contact administrator to request edit permissions.</div>
                {% endif %}"""
    
    rd_content = rd_content.replace(old_buttons, new_buttons)
    
    old_move = """<button type="submit" class="btn btn-warning" onclick="setSubmitAction('move_copy')" style="background-color: #f39c12; border-color: #e67e22;">
                    <span style="font-size:16px; margin-right:4px;">🚚</span> Apply Move/Copy
                </button>"""
    new_move = """{% if is_admin %}
                <button type="submit" class="btn btn-warning" onclick="setSubmitAction('move_copy')" style="background-color: #f39c12; border-color: #e67e22;">
                    <span style="font-size:16px; margin-right:4px;">🚚</span> Apply Move/Copy
                </button>
                {% endif %}"""
    rd_content = rd_content.replace(old_move, new_move)
    
    old_delete = """<button type="button" class="btn btn-danger" onclick="if(confirm('WARNING: Are you sure you want to completely DELETE this record (Row {{ record.row_number }}) from {{ record.sheet }}? This cannot be undone.')){ setSubmitAction('delete'); document.getElementById('editForm').submit(); }" style="float: right;">
                🗑️ Delete Record
            </button>"""
    new_delete = """{% if is_admin %}
            <button type="button" class="btn btn-danger" onclick="if(confirm('WARNING: Are you sure you want to completely DELETE this record (Row {{ record.row_number }}) from {{ record.sheet }}? This cannot be undone.')){ setSubmitAction('delete'); document.getElementById('editForm').submit(); }" style="float: right;">
                🗑️ Delete Record
            </button>
            {% endif %}"""
    rd_content = rd_content.replace(old_delete, new_delete)
    
    with open(rd_path, 'w', encoding='utf-8') as f:
        f.write(rd_content)

# 3. Update load_users in DC_WebApp.py
py_path = os.path.join(APP_DIR, "DC_WebApp.py")
with open(py_path, 'r', encoding='utf-8') as f:
    py_content = f.read()

injection_code = """
        except Exception:
            users = default_users
            
        # Always inject guest user for public demo access
        if "guest" not in users:
            users["guest"] = {
                "password": "guest1",
                "name": "Guest Viewer",
                "role": "user",
                "jurisdiction": "All"
            }
        return users
"""
# We find the try/except block in load_users
if "return default_users" in py_content:
    py_content = re.sub(r'except Exception:\s*return default_users', injection_code.strip(), py_content)
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(py_content)

# 4. Update login.html footer
login_path = os.path.join(TEMPLATES_DIR, "login.html")
with open(login_path, 'r', encoding='utf-8') as f:
    login_content = f.read()
login_content = login_content.replace("Demo: CPF: 2266083 | Password: admin", "Demo: CPF: guest | Password: guest1")
with open(login_path, 'w', encoding='utf-8') as f:
    f.write(login_content)

print("Done updating files!")
