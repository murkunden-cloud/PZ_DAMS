import os
import re

APP_DIR = r"d:\MYPRO\DC\DC_Manager"
py_path = os.path.join(APP_DIR, "DC_WebApp.py")

with open(py_path, 'r', encoding='utf-8') as f:
    py_content = f.read()

# 1. Inject global variables and before_request hook near the top (after app initialization)
hooks_code = """
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    
    # --- TRAFFIC AND SUBSCRIPTION CONTROL ---
    MAX_ACTIVE_GUESTS = 5
    GUEST_SESSION_TIMEOUT_MINUTES = 10
    ACTIVE_GUEST_SESSIONS = {}  # Format: { session_id: last_active_timestamp }

    import time
    import uuid
    from datetime import datetime

    @app.before_request
    def track_guest_sessions():
        # Prune inactive sessions
        current_time = time.time()
        expired = [sid for sid, last_active in ACTIVE_GUEST_SESSIONS.items() 
                   if (current_time - last_active) > (GUEST_SESSION_TIMEOUT_MINUTES * 60)]
        for sid in expired:
            del ACTIVE_GUEST_SESSIONS[sid]

        # Update current user's timestamp if they are a guest
        if "user_cpf" in session and session.get("user_role") == "user":
            sid = session.get("guest_session_id")
            if sid:
                ACTIVE_GUEST_SESSIONS[sid] = current_time
    # ----------------------------------------

    ADMIN_CPF = "2266083"
"""
py_content = py_content.replace('    app.config["SESSION_COOKIE_HTTPONLY"] = True\n    \n    ADMIN_CPF = "2266083"', hooks_code)


# 2. Update login() to handle limits, expires_at, and status
# Locate the login function
login_original = """
    @app.post("/login")
    def login():
        cpf = request.form.get("cpf", "").strip()
        password = request.form.get("password", "").strip()
        users = load_users()
        if cpf in users:
            stored_password = users[cpf]["password"]
            # Check if password is hashed or plain text
            if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
                try:
                    if check_password_hash(stored_password, password):
                        session["user_cpf"] = cpf
                        session["user_name"] = users[cpf]["name"]
                        session["user_role"] = users[cpf].get("role", "client")
                        session["user_jurisdiction"] = users[cpf].get("jurisdiction", "All")
                        return redirect("/home")
                except Exception:
                    # If hash check fails, try plain text as fallback
                    pass
            # Plain text comparison (fallback for migration)
            if stored_password == password:
                session["user_cpf"] = cpf
                session["user_name"] = users[cpf]["name"]
                session["user_role"] = users[cpf].get("role", "client")
                session["user_jurisdiction"] = users[cpf].get("jurisdiction", "All")
                return redirect("/home")
        return render_template("login.html", error="Invalid CPF or Password")
"""

login_replacement = """
    @app.post("/login")
    def login():
        cpf = request.form.get("cpf", "").strip()
        password = request.form.get("password", "").strip()
        users = load_users()
        
        if cpf in users:
            user_data = users[cpf]
            
            # Check subscription / active status
            if user_data.get("status", "active") == "inactive":
                return render_template("login.html", error="Your account has been deactivated. Please contact the administrator.")
                
            # Check automated expiration date
            expires_at = user_data.get("expires_at")
            if expires_at:
                try:
                    exp_date = datetime.strptime(expires_at, "%Y-%m-%d").date()
                    if datetime.now().date() > exp_date:
                        return render_template("login.html", error="Your subscription expired on {}. Please renew to access.".format(expires_at))
                except Exception:
                    pass # Ignore malformed dates
            
            # Check guest traffic limits
            is_guest = user_data.get("role", "user") == "user"
            if is_guest:
                if len(ACTIVE_GUEST_SESSIONS) >= MAX_ACTIVE_GUESTS:
                    return render_template("login.html", error="⚠️ Server is currently at full capacity (Max users reached). Please try again in a few minutes, or contact the administrator to upgrade your tier.")
            
            stored_password = user_data["password"]
            authenticated = False
            
            if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
                try:
                    if check_password_hash(stored_password, password):
                        authenticated = True
                except Exception:
                    pass
                    
            if stored_password == password:
                authenticated = True
                
            if authenticated:
                session["user_cpf"] = cpf
                session["user_name"] = user_data["name"]
                session["user_role"] = user_data.get("role", "user")
                session["user_jurisdiction"] = user_data.get("jurisdiction", "All")
                
                # Track guest session
                if is_guest:
                    sid = str(uuid.uuid4())
                    session["guest_session_id"] = sid
                    ACTIVE_GUEST_SESSIONS[sid] = time.time()
                    
                return redirect("/home")
                
        return render_template("login.html", error="Invalid CPF or Password")
"""
py_content = py_content.replace(login_original.strip(), login_replacement.strip())

# 3. Update logout to clear guest tracking
logout_original = """
    @app.get("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect("/login")
"""
logout_replacement = """
    @app.get("/logout")
    @login_required
    def logout():
        sid = session.get("guest_session_id")
        if sid and sid in ACTIVE_GUEST_SESSIONS:
            del ACTIVE_GUEST_SESSIONS[sid]
        session.clear()
        return redirect("/login")
"""
py_content = py_content.replace(logout_original.strip(), logout_replacement.strip())

with open(py_path, 'w', encoding='utf-8') as f:
    f.write(py_content)

print("Applied traffic control changes!")
