from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from models import create_user, authenticate_user, get_notes, create_note, update_note, delete_note
import uuid

# Initialize FastAPI app
app = FastAPI()

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Secret key for sessions
SECRET = "your-secret-key"

# Simulated session store (in-memory)
sessions = {}


# Function to generate a session ID
def generate_session_id():
    return str(uuid.uuid4())


# Dependency to get the current user
async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized. Please log in first.")
    return sessions[session_id]  # Return user info stored in session


@app.get("/", response_class=HTMLResponse)
async def serve_login_signup_page(request: Request):
    return templates.TemplateResponse("login_signup.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def serve_login_page(request: Request):
    return templates.TemplateResponse("login_signup.html", {"request": request})


@app.post("/register")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    username = username.strip()
    email = email.strip()
    if create_user(username, email, password):
        response = RedirectResponse(url="/login", status_code=303)
        return response
    else:
        raise HTTPException(status_code=400, detail="Email or username already exists.")


@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    user = authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = generate_session_id()
    sessions[session_id] = user

    print(f"User logged in: {user}")
    print(f"Session ID created: {session_id}")

    response = RedirectResponse("/notes", status_code=303)
    response.set_cookie(key="session_id", value=session_id)
    return response


@app.get("/notes", response_class=HTMLResponse)
async def read_notes(request: Request, query: str = "", important_filter: str = "",
                     user: dict = Depends(get_current_user)):
    print(f"Fetching notes for user: {user['username']}")  # Accessing username instead of name
    notes = get_notes(user["email"], query, important_filter)  # Retrieve notes based on user's email
    print(f"Notes retrieved for {user['email']}: {notes}")
    sorted_notes = sorted(notes, key=lambda x: (not x.get("pinned", False), x["_id"]))

    # Pass the user's username for the welcome message
    return templates.TemplateResponse("notes.html",
                                      {"request": request, "newDocs": sorted_notes, "username": user["username"]})  # Updated key to username




@app.post("/notes")
async def create_note_item(request: Request, user: dict = Depends(get_current_user)):
    form = await request.form()
    title = form.get("title")
    desc = form.get("desc")
    important = form.get("important") == "on"
    pinned = form.get("pinned") == "on"

    note_id = create_note(user["email"], title, desc, important, pinned)
    return RedirectResponse("/notes", status_code=303)


@app.post("/notes/update/{note_id}")
async def update_note_item(note_id: str, request: Request, user: dict = Depends(get_current_user)):
    form = await request.form()
    title = form.get("title")
    desc = form.get("desc")
    important = form.get("important") == "on"
    pinned = form.get("pinned") == "on"

    updated = update_note(note_id, user["email"], title, desc, important, pinned)
    if not updated:
        raise HTTPException(status_code=404, detail="Note not found.")

    return RedirectResponse("/notes", status_code=303)


@app.post("/notes/delete/{note_id}")
async def delete_note_item(note_id: str, user: dict = Depends(get_current_user)):
    deleted = delete_note(note_id, user["email"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found.")

    return RedirectResponse("/notes", status_code=303)


@app.post("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")

    if session_id in sessions:
        del sessions[session_id]

    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("session_id")
    return response
