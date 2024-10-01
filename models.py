from pymongo import MongoClient
from bson.objectid import ObjectId
from passlib.context import CryptContext
from typing import Optional, List, Dict
import os
import logging
from fastapi import HTTPException
from dotenv import load_dotenv


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['note_app_db']

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper functions
def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    return pwd_context.verify(plain_password, hashed_password)

# User-related operations
def create_user(username: str, email: str, password: str) -> bool:
    """Create a new user in the database."""
    if db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
        logger.warning(f"User creation failed: User with email {email} or username {username} already exists.")
        return False  # User already exists
    hashed_password = get_password_hash(password)
    db.users.insert_one({"username": username, "email": email, "password": hashed_password})
    logger.info(f"User created successfully: {username}")
    return True

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """Authenticate user by email and password."""
    user = db.users.find_one({"email": email.strip()})
    if user:
        logger.info(f"User found: {user['email']}")
        if verify_password(password.strip(), user['password']):
            logger.info(f"User authenticated successfully: {email}")
            return user
        else:
            logger.warning(f"Incorrect password for email: {email}")
    else:
        logger.warning(f"No user found for email: {email}")
    return None  # Authentication failed

# Notes-related operations
def create_note(user_id: str, title: str, desc: str, important: bool = False, pinned: bool = False) -> ObjectId:
    """Create a new note for a user."""
    note_data = {
        "user_id": user_id,
        "title": title,
        "desc": desc,
        "important": important,
        "pinned": pinned,
    }
    inserted_id = db.notes.insert_one(note_data).inserted_id
    logger.info(f"Note created successfully: {inserted_id} for user {user_id}")
    return inserted_id

def get_notes(user_id: str, query: Optional[str] = "", important_filter: Optional[str] = "") -> List[Dict]:
    """Retrieve all notes for a specific user with optional filters."""
    search_filter = {"user_id": user_id}

    if query:
        search_filter["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
            {"desc": {"$regex": query, "$options": "i"}}
        ]

    if important_filter:
        if important_filter == "important":
            search_filter["important"] = True
        elif important_filter == "not_important":
            search_filter["important"] = False

    notes = list(db.notes.find(search_filter).sort([("pinned", -1), ("_id", -1)]))
    logger.info(f"Retrieved {len(notes)} notes for user {user_id}")
    return notes

def update_note(note_id: str, user_id: str, title: str, desc: str, important: bool, pinned: bool) -> int:
    """Update an existing note by note_id."""
    if not ObjectId.is_valid(note_id):
        logger.error("Invalid note ID format")
        raise ValueError("Invalid note ID format")

    update_data = {
        "title": title,
        "desc": desc,
        "important": important,
        "pinned": pinned
    }
    result = db.notes.update_one({"_id": ObjectId(note_id), "user_id": user_id}, {"$set": update_data})  # Ensure it matches the user

    if result.matched_count == 0:
        logger.error("No note found with the given ID")
        raise ValueError("No note found with the given ID")

    logger.info(f"Note updated successfully: {note_id}")
    return result.modified_count  # Return the number of documents modified

def delete_note(note_id: str, user_id: str) -> int:
    """Delete a note by note_id."""
    if not ObjectId.is_valid(note_id):
        logger.error("Invalid note ID format")
        raise ValueError("Invalid note ID format")

    deleted_count = db.notes.delete_one({"_id": ObjectId(note_id), "user_id": user_id}).deleted_count
    logger.info(f"Note deleted: {note_id} for user {user_id}")
    return deleted_count
