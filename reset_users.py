import json
import os

# Default users configuration
default_users = {
    "2266083": {
        "password": "admin",
        "name": "Nagesh D. M",
        "role": "admin",
        "jurisdiction": "All"
    },
    "rastapeth": {
        "password": "password",
        "name": "Rastapeth Circle",
        "role": "user",
        "jurisdiction": "Rastapeth Urban Circle"
    },
    "ganeshkhind": {
        "password": "password",
        "name": "Ganeshkhind Circle",
        "role": "user",
        "jurisdiction": "Ganeshkhind Urban Circle"
    },
    "punerural": {
        "password": "password",
        "name": "Pune Rural Circle",
        "role": "user",
        "jurisdiction": "Pune Rural Circle"
    }
}

# Path to users.json
users_file = os.path.join(os.path.dirname(__file__), "runtime", "users.json")

# Backup existing file if it exists
if os.path.exists(users_file):
    backup_file = users_file + ".backup"
    with open(users_file, "r", encoding="utf-8") as f:
        existing_data = f.read()
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(existing_data)
    print(f"Backup created at: {backup_file}")

# Write default users
with open(users_file, "w", encoding="utf-8") as f:
    json.dump(default_users, f, indent=4)

print(f"Users file reset to default at: {users_file}")
print("\nDefault credentials restored:")
print("- Admin (2266083): Password = admin")
print("- Rastapeth: Password = password")
print("- Ganeshkhind: Password = password")
print("- Pune Rural: Password = password")
print("\nGuest user will be automatically added by the system.")
