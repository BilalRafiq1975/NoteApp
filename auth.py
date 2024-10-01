from datetime import datetime
from typing import Union  # Import Union from typing

# Simulated session store (in-memory)
sessions = {}

# Generate a session ID (you can customize this as needed)
def generate_session_id():
    return str(len(sessions) + 1)

# Function to get the current user from the session store
def get_current_user(session_id: str):
    return sessions.get(session_id)

# You can use this method when creating a session after user login
def create_user_session(user_data: dict):
    session_id = generate_session_id()
    sessions[session_id] = user_data  # Store user data in the session
    return session_id

# Function to remove user session on logout
def logout_user(session_id: str):
    if session_id in sessions:
        del sessions[session_id]  # Remove user session

# Example usage (these would be called in your FastAPI routes)
# When a user logs in, create a session
def login_user(email: str):
    user_data = {"email": email}  # Fetch user data based on email (you can include more data if needed)
    return create_user_session(user_data)

# When a user logs out, remove the session
def logout(email: str):
    session_id = next((sid for sid, user in sessions.items() if user["email"] == email), None)
    if session_id:
        logout_user(session_id)
