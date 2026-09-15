import os
import secrets
import time

import duckdb
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import HfFileSystem
from pydantic import BaseModel


# ============================================================
# CONFIGURATION
# ============================================================

ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD")
HF_TOKEN = os.environ.get("HF_TOKEN")

if not ACCESS_PASSWORD:
    raise RuntimeError("ACCESS_PASSWORD is not configured.")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is not configured.")


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="DARULDARK Number Lookup API",
    version="1.0.0",
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================
# HUGGING FACE FILESYSTEM
# ============================================================

hf_fs = HfFileSystem(token=HF_TOKEN)


# ============================================================
# DATABASES
# ============================================================

DATABASES = {
    "bsnl": {
        "name": "BSNL Mobile",
        "file": "19M-BSNL_Mobile.parquet",
        "url": "hf://buckets/daruldark/tele1/19M-BSNL_Mobile.parquet",
    },
    "idea1": {
        "name": "Idea Part 01",
        "file": "50M-Idea_part01.parquet",
        "url": "hf://buckets/daruldark/tele1/50M-Idea_part01.parquet",
    },
    "idea2": {
        "name": "Idea Part 02",
        "file": "50M-Idea_part02.parquet",
        "url": "hf://buckets/daruldark/tele1/50M-Idea_part02.parquet",
    },
}


# ============================================================
# SESSION STORAGE
# ============================================================

SESSIONS = {}

SESSION_DURATION = 8 * 60 * 60  # 8 hours

SESSION_COOKIE = "daruldark_session"


# ============================================================
# REQUEST MODELS
# ============================================================

class LoginRequest(BaseModel):
    password: str


# ============================================================
# HELPERS
# ============================================================

def create_session():
    session_id = secrets.token_urlsafe(32)

    SESSIONS[session_id] = {
        "created": time.time(),
        "expires": time.time() + SESSION_DURATION,
    }

    return session_id


def get_session(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)

    if not session_id:
        return None

    session = SESSIONS.get(session_id)

    if not session:
        return None

    if time.time() > session["expires"]:
        SESSIONS.pop(session_id, None)
        return None

    return session


def require_session(request: Request):
    session = get_session(request)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    return session


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "DARULDARK Number Lookup API",
        "developer": "daruldark",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "developer": "daruldark",
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
def login(data: LoginRequest):
    if not secrets.compare_digest(
        data.password,
        ACCESS_PASSWORD
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid password.",
        )

    session_id = create_session()

    response = {
        "status": "success",
        "message": "Login successful.",
        "developer": "daruldark",
    }

    from fastapi.responses import JSONResponse

    result = JSONResponse(content=response)

    result.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=SESSION_DURATION,
    )

    return result


# ============================================================
# SESSION CHECK
# ============================================================

@app.get("/api/session")
def session_status(request: Request):
    session = get_session(request)

    if not session:
        return {
            "authenticated": False,
            "developer": "daruldark",
        }

    return {
        "authenticated": True,
        "developer": "daruldark",
    }


# ============================================================
# LOGOUT
# ============================================================

@app.post("/api/logout")
def logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)

    if session_id:
        SESSIONS.pop(session_id, None)

    from fastapi.responses import JSONResponse

    response = JSONResponse(
        content={
            "status": "success",
            "message": "Logged out.",
            "developer": "daruldark",
        }
    )

    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response


# ============================================================
# DATABASE LIST
# ============================================================

@app.get("/api/databases")
def list_databases(request: Request):
    require_session(request)

    databases = []

    for database_id, database in DATABASES.items():
        databases.append(
            {
                "id": database_id,
                "name": database["name"],
                "file": database["file"],
            }
        )

    return {
        "status": "success",
        "databases": databases,
        "developer": "daruldark",
    }


# ============================================================
# LOOKUP
# ============================================================

@app.get("/api/lookup")
def lookup(
    request: Request,
    database: str,
    number: str,
):
    require_session(request)

    # --------------------------------------------------------
    # Validate database
    # --------------------------------------------------------

    database_key = database.lower().strip()

    if database_key not in DATABASES:
        raise HTTPException(
            status_code=400,
            detail="Invalid database.",
        )

    database_info = DATABASES[database_key]

    # --------------------------------------------------------
    # Clean number
    # --------------------------------------------------------

    number = number.strip()

    if not number:
        raise HTTPException(
            status_code=400,
            detail="Number is required.",
        )

    # Only accept digits.
    if not number.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Number must contain digits only.",
        )

    # --------------------------------------------------------
    # Database connection
    # --------------------------------------------------------

    con = None

    try:
        con = duckdb.connect()

        # Register authenticated Hugging Face filesystem.
        con.register_filesystem(hf_fs)

        file_url = database_info["url"]

        # ----------------------------------------------------
        # Query
        #
        # The database path is selected only from our fixed
        # DATABASES mapping above. The phone number remains a
        # prepared parameter.
        # ----------------------------------------------------

        query = f"""
            SELECT *
            FROM read_parquet('{file_url}')
            WHERE "Number" = ?
            LIMIT 1
        """

        result = con.execute(
            query,
            [number],
        )

        # Get column names.
        columns = [
            description[0]
            for description in result.description
        ]

        row = result.fetchone()

        matched = row is not None

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Do not return the actual row values through the
        # public website/API response.
        # ----------------------------------------------------

        return {
            "status": "success",
            "database": database_info["name"],
            "database_file": database_info["file"],
            "matched": matched,
            "columns_available": columns,
            "developer": "daruldark",
        }

    except Exception as error:

        # Detailed error goes only to Render server logs.
        print(
            "DATABASE ERROR:",
            repr(error),
            flush=True,
        )

        return {
            "status": "error",
            "message": "Database operation failed.",
            "developer": "daruldark",
        }

    finally:

        if con is not None:
            try:
                con.close()
            except Exception:
                pass


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )