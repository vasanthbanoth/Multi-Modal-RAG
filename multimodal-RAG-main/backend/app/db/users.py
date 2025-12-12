"""
User database module - provides basic user management functions.
This is a stub implementation; replace with real database queries as needed.
"""

# Mock user database (in production, this would be a real database)
_users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lm",  # password: "secret"
        "disabled": False,
    }
}


def get_user(email: str) -> dict | None:
    """
    Retrieve a user by email from the database.
    
    Args:
        email: The user's email address
        
    Returns:
        User dictionary or None if not found
    """
    return _users_db.get(email)


def create_user(email: str, full_name: str, hashed_password: str) -> dict:
    """
    Create a new user in the database.
    
    Args:
        email: The user's email address
        full_name: The user's full name
        hashed_password: The bcrypt-hashed password
        
    Returns:
        The created user dictionary
    """
    user = {
        "email": email,
        "full_name": full_name,
        "hashed_password": hashed_password,
        "disabled": False,
    }
    _users_db[email] = user
    return user


def update_user(email: str, **kwargs) -> dict | None:
    """
    Update a user's information.
    
    Args:
        email: The user's email address
        **kwargs: Fields to update
        
    Returns:
        Updated user dictionary or None if not found
    """
    user = _users_db.get(email)
    if user:
        user.update(kwargs)
    return user


def delete_user(email: str) -> bool:
    """
    Delete a user from the database.
    
    Args:
        email: The user's email address
        
    Returns:
        True if deleted, False if not found
    """
    if email in _users_db:
        del _users_db[email]
        return True
    return False
