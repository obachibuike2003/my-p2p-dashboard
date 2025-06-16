from werkzeug.security import generate_password_hash

# --- The admin password you want to hash ---
admin_password = "MULLER2003"

# Generate the hash using PBKDF2 with SHA256, as expected by your backend
# The 'method' parameter explicitly tells Werkzeug which algorithm to use.
hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')

print("--------------------------------------------------")
print("Your Werkzeug PBKDF2-SHA256 Hash for 'MULLER2003' is:")
print(hashed_password)
print("--------------------------------------------------")
print("\nCopy this hash carefully. This is what you should put in Railway.")