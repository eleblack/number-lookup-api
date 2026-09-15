from fastapi import FastAPI, Request, Query, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

import os
import time
import hmac
import hashlib
import secrets

import duckdb
from huggingface_hub import HfFileSystem


# =========================================================
# NUMBER API
# =========================================================

app = FastAPI(
    title="NUMBER API",
    description="DARULDARK authorized database lookup API",
    version="2.0.0"
)


# =========================================================
# WEBSITE / CORS
# =========================================================

WEBSITE_ORIGIN = "https://number-5h6b.onrender.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        WEBSITE_ORIGIN,
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# =========================================================
# SECRETS
# =========================================================

API_KEY = os.environ.get("DARULDARK_API_KEY")
SITE_PASSWORD = os.environ.get("NUMBER_SITE_PASSWORD")

# Random signing secret used for website login sessions.
# Set this in Render for persistent sessions across restarts.
SESSION_SECRET = os.environ.get("NUMBER_SESSION_SECRET")

if not API_KEY:
    print("WARNING: DARULDARK_API_KEY is not configured.")

if not SITE_PASSWORD:
    print("WARNING: NUMBER_SITE_PASSWORD is not configured.")

if not SESSION_SECRET:
    print("WARNING: NUMBER_SESSION_SECRET is not configured.")


# =========================================================
# DATABASE CONNECTION
# =========================================================

con = duckdb.connect()

hf_fs = HfFileSystem(token=False)
con.register_filesystem(hf_fs)


DATABASES = {
    "bsnl": {
        "name": "BSNL Mobile",
        "file": "19M-BSNL_Mobile.parquet",
        "url": "hf://buckets/daruldark/tele1/19M-BSNL_Mobile.parquet",
        "size": "402 MB"
    },

    "idea_part01": {
        "name": "Idea Part 01",
        "file": "50M-Idea_part01.parquet",
        "url": "hf://buckets/daruldark/tele1/50M-Idea_part01.parquet",
        "size": "525 MB"
    },

    "idea_part02": {
        "name": "Idea Part 02",
        "file": "50M-Idea_part02.parquet",
        "url": "hf://buckets/daruldark/tele1/50M-Idea_part02.parquet",
        "size": "410 MB"
    }
}


# =========================================================
# SIMPLE LOGIN SESSION
# =========================================================

SESSION_COOKIE = "number_session"

# In-memory sessions.
# Render may restart the free instance, which simply logs users out.
sessions = {}

# Basic login rate limiting.
login_attempts = {}


def create_session() -> str:
    """
    Create a random session ID.
    The ID itself contains no user information.
    """

    session_id = secrets.token_urlsafe(32)

    sessions[session_id] = {
        "created": time.time(),
        "last_seen": time.time()
    }

    return session_id


def valid_session(session_id: str | None) -> bool:
    if not session_id:
        return False

    session = sessions.get(session_id)

    if not session:
        return False

    # Session expires after 12 hours.
    if time.time() - session["created"] > 12 * 60 * 60:
        sessions.pop(session_id, None)
        return False

    session["last_seen"] = time.time()

    return True


def delete_session(session_id: str | None):
    if session_id:
        sessions.pop(session_id, None)


# =========================================================
# ERROR HANDLING
# =========================================================

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "status": "rejected",
                "message": "Invalid endpoint.",
                "Developer": "daruldark"
            }
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "Developer": "daruldark"
        }
    )


# =========================================================
# HOME
# =========================================================

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "NUMBER API",
        "Developer": "daruldark",
        "website": WEBSITE_ORIGIN,
        "databases": list(DATABASES.keys())
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "NUMBER API",
        "Developer": "daruldark"
    }


# =========================================================
# DATABASE LIST
# =========================================================

@app.get("/api/databases")
async def databases():
    return {
        "status": "success",
        "Developer": "daruldark",
        "databases": [
            {
                "id": database_id,
                "name": database["name"],
                "file": database["file"],
                "size": database["size"]
            }
            for database_id, database in DATABASES.items()
        ]
    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/api/login")
async def login(request: Request):
    if not SITE_PASSWORD:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Website authentication is not configured.",
                "Developer": "daruldark"
            }
        )

    client_ip = request.client.host if request.client else "unknown"

    now = time.time()

    # Keep only attempts from the last 10 minutes.
    attempts = login_attempts.get(client_ip, [])

    attempts = [
        timestamp
        for timestamp in attempts
        if now - timestamp < 600
    ]

    # Maximum 10 login attempts per 10 minutes per IP.
    if len(attempts) >= 10:
        return JSONResponse(
            status_code=429,
            content={
                "status": "rejected",
                "message": "Too many login attempts. Try again later.",
                "Developer": "daruldark"
            }
        )

    login_attempts[client_ip] = attempts

    try:
        body = await request.json()
    except Exception:
        body = {}

    password = str(body.get("password", ""))

    login_attempts[client_ip].append(now)

    if not hmac.compare_digest(password, SITE_PASSWORD):
        return JSONResponse(
            status_code=401,
            content={
                "status": "rejected",
                "message": "Invalid password.",
                "Developer": "daruldark"
            }
        )

    session_id = create_session()

    response = JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Login successful.",
            "Developer": "daruldark"
        }
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=12 * 60 * 60,
        path="/"
    )

    return response


# =========================================================
# SESSION STATUS
# =========================================================

@app.get("/api/session")
async def session_status(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)

    if valid_session(session_id):
        return {
            "status": "authenticated",
            "Developer": "daruldark"
        }

    return JSONResponse(
        status_code=401,
        content={
            "status": "unauthenticated",
            "Developer": "daruldark"
        }
    )


# =========================================================
# LOGOUT
# =========================================================

@app.post("/api/logout")
async def logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)

    delete_session(session_id)

    response = JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Logged out.",
            "Developer": "daruldark"
        }
    )

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/"
    )

    return response


# =========================================================
# LOOKUP
# =========================================================

@app.get("/api/lookup")
async def lookup(
    request: Request,
    number: str = Query(..., description="Number to search"),
    database: str = Query(
        "bsnl",
        description="Database ID"
    ),
    x_api_key: str | None = Header(default=None)
):

    # -----------------------------------------------------
    # Authentication
    #
    # Website users authenticate through the HttpOnly cookie.
    # Server/API clients can authenticate with X-API-Key.
    # -----------------------------------------------------

    session_id = request.cookies.get(SESSION_COOKIE)

    authenticated_by_session = valid_session(session_id)

    authenticated_by_api_key = (
        API_KEY is not None
        and x_api_key is not None
        and hmac.compare_digest(x_api_key, API_KEY)
    )

    if not authenticated_by_session and not authenticated_by_api_key:
        return JSONResponse(
            status_code=401,
            content={
                "status": "rejected",
                "message": "Authentication required.",
                "Developer": "daruldark"
            }
        )

    # -----------------------------------------------------
    # Database validation
    # -----------------------------------------------------

    if database not in DATABASES:
        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Unknown database.",
                "available_databases": list(DATABASES.keys()),
                "Developer": "daruldark"
            }
        )

    # -----------------------------------------------------
    # Number validation
    # -----------------------------------------------------

    number = number.strip()

    if (
        not number
        or not number.isdigit()
        or len(number) < 10
        or len(number) > 15
    ):
        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Invalid number.",
                "Developer": "daruldark"
            }
        )

    selected_database = DATABASES[database]

    file_url = selected_database["url"]

    # -----------------------------------------------------
    # Database query
    # -----------------------------------------------------

    try:
        query = """
            SELECT 1
            FROM read_parquet(?)
            WHERE "Number" = ?
            LIMIT 1
        """

        result = con.execute(
            query,
            [file_url, number]
        )

        row = result.fetchone()

        if row is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "database": selected_database["name"],
                    "matched": False,
                    "Developer": "daruldark"
                }
            )

        # -------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT return the database row here.
        # This intentionally prevents names, addresses,
        # emails, social accounts, etc. from being exposed
        # through the public website/API response.
        # -------------------------------------------------

        return {
            "status": "success",
            "database": selected_database["name"],
            "database_file": selected_database["file"],
            "matched": True,
            "Developer": "daruldark"
        }

    except Exception as exc:
        print("Database error:", repr(exc))

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Database operation failed.",
                "Developer": "daruldark"
            }
        )


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":
    import uvicorn

    port = int(
        os.environ.get("PORT", 8080)
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )