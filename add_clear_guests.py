import os
import re

APP_DIR = r"d:\MYPRO\DC\DC_Manager"
py_path = os.path.join(APP_DIR, "DC_WebApp.py")
base_html_path = os.path.join(APP_DIR, "templates", "base.html")

# 1. Update DC_WebApp.py to add the clear_guests route
with open(py_path, 'r', encoding='utf-8') as f:
    py_content = f.read()

route_code = """
    @app.post("/admin/clear_guests")
    @admin_required
    def clear_guest_sessions():
        count = len(ACTIVE_GUEST_SESSIONS)
        ACTIVE_GUEST_SESSIONS.clear()
        # Optionally pass a message, but we just redirect
        return redirect(request.referrer or "/home")
"""

# Inject before the logout route
if '    @app.get("/logout")' in py_content:
    py_content = py_content.replace('    @app.get("/logout")', route_code.strip() + '\n\n    @app.get("/logout")')
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(py_content)

# 2. Update base.html to add the button
with open(base_html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# We look for the "Utility & Maintenance" section where admin links are.
button_html = """
                {% if is_admin %}
                <li>
                    <a href="#" onclick="if(confirm('Force logout all active guest sessions? This will immediately free up capacity.')){ document.getElementById('clear-guests-form').submit(); } return false;" style="color: #e74c3c; font-weight: bold;">
                        🧹 Clear Active Guests
                    </a>
                </li>
                {% endif %}
                <li><a href="/users" id="nav-users">👥 Manage Users</a></li>
"""

if '<li><a href="/users" id="nav-users">👥 Manage Users</a></li>' in html_content:
    html_content = html_content.replace('<li><a href="/users" id="nav-users">👥 Manage Users</a></li>', button_html.strip())

# Add the hidden form for clear guests next to the exit form
form_html = """
            <!-- Hidden Clear Guests Form -->
            <form id="clear-guests-form" action="/admin/clear_guests" method="post" style="display: none;"></form>
            
            <!-- Hidden Exit Form -->
"""
if '<!-- Hidden Exit Form -->' in html_content:
    html_content = html_content.replace('<!-- Hidden Exit Form -->', form_html.strip())

with open(base_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Added clear guests button successfully!")
