from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import mysql.connector
import bcrypt

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates directory
templates = Jinja2Templates(directory="templates")

# MySQL Database connection
db_config = {
    'user': 'root',  # Replace with your MySQL username
    'password': '12345',  # Replace with your MySQL password
    'host': 'localhost',  # or the host where your MySQL server is running
    'database': 'user_det'
}

# Establish connection to MySQL
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Function to validate user credentials
def validate_user(username, password):
    try:
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result:
            stored_hash = result[0]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return True
        return False
    except mysql.connector.Error as err:
        print(f"Error during user validation: {err}")
        return False

# Function to add a new user
def add_user(username, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()

# Route to serve the HTML sign-in page
@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("sign.html", {"request": request})

# Route to handle login submission
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if validate_user(username, password):
        # Redirect to payment page with welcome flag
        url = f"/payment?username={username}&welcome=true"
        return RedirectResponse(url=url)
    else:
        raise HTTPException(status_code=400, detail="Invalid username or password")

# Route to handle user registration
@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...)):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Add the new user
    add_user(username, password)

    # Redirect to payment page without welcome flag
    url = f"/payment?username={username}&welcome=false"
    return RedirectResponse(url=url)

# Payment page route
@app.post("/payment", response_class=HTMLResponse)
async def payment(request: Request, username: str, welcome: str):
    is_welcome = True if welcome == "true" else False
    return templates.TemplateResponse("pay.html", {"request": request, "username": username, "is_welcome": is_welcome})

@app.get("/proceed-payment", response_class=HTMLResponse)
async def proceed_payment(request: Request):
    # Redirect to pay2.html when "Proceed Payment" is clicked
    return templates.TemplateResponse("/static/pay1.html", {"request": request})