from backend.app.core.security import get_password_hash

# In-memory user database for demonstration
# In a real application, this would be a proper database (SQL, NoSQL, etc.)
FAKE_USERS_DB = {
    "user@example.com": {
        "email": "user@example.com",
        "hashed_password": get_password_hash("password123"),
        "full_name": "Example User",
        "disabled": False,
    }
}

def get_user(email: str):
    """
    Retrieves a user from the fake database by email.
    """
    if email in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[email]
        return user_dict
    return None