import bcrypt

def generate_password_hash(password: str) -> bytes:
    """
    Generate a bcrypt hash for the given password.
    
    Args:
        password (str): The plain text password to hash
        
    Returns:
        bytes: The hashed password
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
        
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Convert the password to bytes and generate salt
    password_bytes = password.encode('utf-8')
    # Use bcrypt.gensalt(12) to specify rounds (default is 12)
    salt = bcrypt.gensalt(12)
    
    # Generate the hashed password
    hashed = bcrypt.hashpw(password_bytes, salt)

    hashed_decoded = hashed.decode('utf-8')
    
    return hashed_decoded

def compare_hashed_password(password: str, hashed_password: str | bytes) -> bool:
    """
    Compare a plain text password against a hashed password.
    
    Args:
        password (str): The plain text password to check
        hashed_password (str|bytes): The hashed password to compare against
        
    Returns:
        bool: True if passwords match, False otherwise
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    
    try:
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Ensure hashed_password is bytes
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
            
        # Verify the hash format
        if not hashed_bytes.startswith(b'$2b$') and not hashed_bytes.startswith(b'$2a$'):
            raise ValueError("Invalid hash format")
            
        return bcrypt.checkpw(password_bytes, hashed_bytes)
        
    except (ValueError, TypeError) as e:
        print(f"Password comparison failed: {str(e)}")
        return False