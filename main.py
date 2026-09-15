import os
import secrets
import time
from datetime import datetime, timezone

import duckdb
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from huggingface_hub import HfFileSystem
from pydantic import BaseModel


# ============================================================
# CONFIG
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
    title="DARULDARK Private Admin API",
    version="2.0.0",
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
# HUGGING FACE
# ============================================================

hf_fs = HfFileSystem(token=HF_TOKEN)


# ============================================================
# DATABASES
# ============================================================

DATABASES = {
    "bsnl": {
        "name": "BSNL Mobile",
        "file": "19M-BSNL_Mobile.parquet",
        "url": (
            "hf://buckets/daruldark/tele1/"
            "19M-BSNL_Mobile.parquet"
        ),
    },
    "idea1": {
        "name": "Idea Part 01",
        "file": "50M-Idea_part01.parquet",
        "url": (
            "hf://buckets/daruldark/tele1/"
            "50M-Idea_part01.parquet"
        ),
    },
    "idea2": {
        "name": "Idea Part 02",
        "file": "50M-Idea_part02.parquet"
        ,
        "url": (
            "hf://buckets/daruldark/tele1/"
            "50M-Idea_part02.parquet"
        ),
    },
}


# ============================================================
# FIELDS ALLOWED IN THE ADMIN RESPONSE
#
# Keep this list intentionally small.
# ============================================================

DISPLAY_FIELDS = [
    "Number",
    "Carrier",
]


# ============================================================
# SESSIONS
# ============================================================

SESSIONS = {}

SESSION_DURATION = 8 * 60 * 60

SESSION_COOKIE = "daruldark_session"


# ============================================================
# LOGIN MODEL
# ============================================================

class LoginRequest(BaseModel):
    password: str


# ============================================================
# SESSION HELPERS
# ============================================================

def create_session():
    session_id = secrets.token_urlsafe(32)

    now = time.time()

    SESSIONS[session_id] = {
        "created": now,
        "expires": now + SESSION_DURATION,
    }

    return session_id


def get_session(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)

    if not session_id:
        return None

    session = SESSIONS.get(session_id)

    if not session:
        return None

    if time.time() >= session["expires"]:
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
# AUDIT LOG
# ============================================================

def audit(event, database=None):
    timestamp = datetime.now(timezone.utc).isoformat()

    print(
        f"AUDIT | {timestamp} | {event}"
        + (
            f" | database={database}"
            if database
            else ""
        ),
        flush=True,
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "DARULDARK Private Admin API",
        "developer": "daruldark",
    }


# ============================================================
# HEALTH
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
        ACCESS_PASSWORD,
    ):
        audit("failed_login")

        raise HTTPException(
            status_code=401,
            detail="Invalid password.",
        )

    session_id = create_session()

    audit("successful_login")

    response = JSONResponse(
        content={
            "status": "success",
            "message": "Login successful.",
            "developer": "daruldark",
        }
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=SESSION_DURATION,
    )

    return response


# ============================================================
# SESSION
# ============================================================

@app.get("/api/session")
def session_status(request: Request):

    session = get_session(request)

    return {
        "authenticated": session is not None,
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

    audit("logout")

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
# DATABASES
# ============================================================

@app.get("/api/databases")
def list_databases(request: Request):

    require_session(request)

    return {
        "status": "success",
        "databases": [
            {
                "id": database_id,
                "name": database["name"],
                "file": database["file"],
            }
            for database_id, database in DATABASES.items()
        ],
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

    database_key = database.strip().lower()

    if database_key not in DATABASES:
        raise HTTPException(
            status_code=400,
            detail="Invalid database.",
        )

    number = number.strip()

    if not number:
        raise HTTPException(
            status_code=400,
            detail="Number is required.",
        )

    if not number.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Number must contain digits only.",
        )

    database_info = DATABASES[database_key]

    con = None

    try:
        con = duckdb.connect()

        con.register_filesystem(hf_fs)

        file_url = database_info["url"]

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

        columns = [
            description[0]
            for description in result.description
        ]

        row = result.fetchone()

        audit(
            "lookup",
            database=database_info["name"],
        )

        if row is None:
            return {
                "status": "success",
                "database": database_info["name"],
                "database_file": database_info["file"],
                "matched": False,
                "details": {},
                "developer": "daruldark",
            }

        # Convert only the approved fields.
        row_data = dict(zip(columns, row))

        safe_details = {}

        for field in DISPLAY_FIELDS:
            if field in row_data:
                safe_details[field] = row_data[field]

        return {
            "status": "success",
            "database": database_info["name"],
            "database_file": database_info["file"],
            "matched": True,
            "details": safe_details,
            "developer": "daruldark",
        }

    except Exception as error:

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
# SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.environ.get("PORT", "8000")
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )