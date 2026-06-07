import json
import hashlib
import os

USERS_FILE = ".users.json"

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def main():
    while True:
        print("\n=== Omega OS User Management ===")
        print("1. List Users")
        print("2. Add User")
        print("3. Remove User")
        print("4. Exit")
        choice = input("Select an option (1-4): ").strip()
        
        users = load_users()
        
        if choice == "1":
            print("\n--- Current Users ---")
            if not users:
                print("No users found.")
            else:
                for uid in users:
                    print(f"- {uid}")
                    
        elif choice == "2":
            uid = input("Enter new User ID: ").strip()
            if not uid:
                print("User ID cannot be empty.")
                continue
            if uid in users:
                print("User already exists!")
                continue
            pwd = input("Enter Password: ").strip()
            if not pwd:
                print("Password cannot be empty.")
                continue
            users[uid] = get_password_hash(pwd)
            save_users(users)
            print(f"User '{uid}' added successfully.")
            
        elif choice == "3":
            uid = input("Enter User ID to remove: ").strip()
            if uid in users:
                del users[uid]
                save_users(users)
                print(f"User '{uid}' removed successfully.")
            else:
                print(f"User '{uid}' not found.")
                
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
