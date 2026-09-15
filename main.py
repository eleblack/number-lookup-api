from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from starlette.exceptions import HTTPException as StarletteHTTPException

import os
import secrets
import time
import duckdb
from huggingface_hub import HfFileSystem


# ============================================================
# DARULDARK NUMBER LOOKUP API
# ============================================================

app = FastAPI(
    title="DARULDARK Number Lookup API",
    description="Authorized database lookup API",
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://number-5h6b.onrender.com",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ============================================================
# SERVER-SIDE AUTHENTICATION
# ============================================================

# Set this in Render:
#
# ACCESS_PASSWORD=darul123
#
# For local testing:
#
# PowerShell:
# $env:ACCESS_PASSWORD="darul123"

ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD")

if not ACCESS_PASSWORD:
    print("WARNING: ACCESS_PASSWORD is not configured.")


# Random session tokens.
# Sessions disappear when the Render service restarts.
SESSIONS = {}

SESSION_COOKIE = "daruldark_session"

SESSION_DURATION = 60 * 60 * 8  # 8 hours


def create_session():
    token = secrets.token_urlsafe(32)

    SESSIONS[token] = {
        "created": time.time()
    }

    return token


def valid_session(token):
    if not token:
        return False

    session = SESSIONS.get(token)

    if not session:
        return False

    if time.time() - session["created"] > SESSION_DURATION:
        SESSIONS.pop(token, None)
        return False

    return True


def remove_session(token):
    if token:
        SESSIONS.pop(token, None)


# ============================================================
# DATABASE CONNECTION
# ============================================================

con = duckdb.connect()

hf_fs = HfFileSystem(token=False)
con.register_filesystem(hf_fs)


# ============================================================
# DATABASES
# ============================================================

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


# ============================================================
# ERROR HANDLER
# ============================================================

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


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "DARULDARK Number Lookup API",
        "Developer": "daruldark",
        "authentication": "required",
        "databases": list(DATABASES.keys())
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "DARULDARK Number Lookup API",
        "Developer": "daruldark"
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
async def login(request: Request):

    if not ACCESS_PASSWORD:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Server authentication is not configured.",
                "Developer": "daruldark"
            }
        )

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Invalid request.",
                "Developer": "daruldark"
            }
        )

    password = str(body.get("password", ""))

    if not secrets.compare_digest(password, ACCESS_PASSWORD):
        return JSONResponse(
            status_code=401,
            content={
                "status": "rejected",
                "message": "Incorrect password.",
                "Developer": "daruldark"
            }
        )

    session_token = create_session()

    response = JSONResponse(
        content={
            "status": "success",
            "message": "Login successful.",
            "Developer": "daruldark"
        }
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="none"
    )

    return response


# ============================================================
# LOGOUT
# ============================================================

@app.post("/api/logout")
async def logout(request: Request):

    token = request.cookies.get(SESSION_COOKIE)

    remove_session(token)

    response = JSONResponse(
        content={
            "status": "success",
            "message": "Logged out.",
            "Developer": "daruldark"
        }
    )

    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=True,
        samesite="none"
    )

    return response


# ============================================================
# SESSION CHECK
# ============================================================

@app.get("/api/session")
async def session(request: Request):

    token = request.cookies.get(SESSION_COOKIE)

    if valid_session(token):
        return {
            "authenticated": True,
            "Developer": "daruldark"
        }

    return {
        "authenticated": False,
        "Developer": "daruldark"
    }


# ============================================================
# DATABASE LIST
# ============================================================

@app.get("/api/databases")
async def databases(request: Request):

    token = request.cookies.get(SESSION_COOKIE)

    if not valid_session(token):
        return JSONResponse(
            status_code=401,
            content={
                "status": "rejected",
                "message": "Login required.",
                "Developer": "daruldark"
            }
        )

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


# ============================================================
# AUTHENTICATED LOOKUP
# ============================================================

@app.get("/api/lookup")
async def lookup(
    request: Request,
    number: str = Query(...),
    database: str = Query("bsnl")
):

    # --------------------------------------------------------
    # Check login
    # --------------------------------------------------------

    token = request.cookies.get(SESSION_COOKIE)

    if not valid_session(token):
        return JSONResponse(
            status_code=401,
            content={
                "status": "rejected",
                "message": "Please login before using the API.",
                "Developer": "daruldark"
            }
        )

    # --------------------------------------------------------
    # Validate database
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Validate number
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Query database
    # --------------------------------------------------------

    try:

        query = """
            SELECT *
            FROM read_parquet(?)
            WHERE "Number" = ?
            LIMIT 1
        """

        result = con.execute(
            query,
            [file_url, number]
        )

        columns = [
            description[0]
            for description in result.description
        ]

        row = result.fetchone()

        if row is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "database": selected_database["name"],
                    "database_file": selected_database["file"],
                    "matched": False,
                    "Developer": "daruldark"
                }
            )

        # ----------------------------------------------------
        # Do not expose the personal-data values through the
        # public website/API response.
        # ----------------------------------------------------

        return {
            "status": "success",
            "database": selected_database["name"],
            "database_file": selected_database["file"],
            "matched": True,
            "columns_available": columns,
            "Developer": "daruldark"
        }

    except Exception as error:

        print("Database error:", error)

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Database operation failed.",
                "Developer": "daruldark"
            }
        )


# ============================================================
# LOCAL START
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )