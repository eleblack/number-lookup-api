from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

import os
import duckdb
from huggingface_hub import HfFileSystem


# ============================================================
# NUMBER API
# ============================================================

app = FastAPI(
    title="NUMBER API",
    description="DARULDARK Number Database API",
    version="1.0.0"
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
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

con = duckdb.connect()

hf_fs = HfFileSystem(token=False)
con.register_filesystem(hf_fs)


DATABASES = {
    "bsnl": {
        "name": "BSNL Mobile",
        "file": "19M-BSNL_Mobile.parquet",
        "url": "hf://buckets/daruldark/tele1/19M-BSNL_Mobile.parquet",
        "size": "402 MB",
    },

    "idea_part01": {
        "name": "Idea Part 01",
        "file": "50M-Idea_part01.parquet",
        "url": "hf://buckets/daruldark/tele1/50M-Idea_part01.parquet",
        "size": "525 MB",
    },

    "idea_part02": {
        "name": "Idea Part 02",
        "file": "50M-Idea_part02.parquet",
        "url": "hf://buckets/daruldark/tele1/50M-Idea_part02.parquet",
        "size": "410 MB",
    },
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
                "Developer": "daruldark",
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "Developer": "daruldark",
        },
    )


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "NUMBER API",
        "Developer": "daruldark",
        "website": "number-5h6b.onrender.com",
        "access": "direct",
        "databases": list(DATABASES.keys()),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "NUMBER API",
        "Developer": "daruldark",
    }


# ============================================================
# DATABASE LIST
# ============================================================

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
                "size": database["size"],
            }
            for database_id, database in DATABASES.items()
        ],
    }


# ============================================================
# NUMBER LOOKUP
# ============================================================

@app.get("/api/lookup")
async def lookup(
    number: str = Query(..., description="Number to search"),
    database: str = Query(
        "bsnl",
        description="Database ID"
    ),
):

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
                "Developer": "daruldark",
            },
        )

    # --------------------------------------------------------
    # Clean number
    # --------------------------------------------------------

    number = number.strip()

    # --------------------------------------------------------
    # Validate number
    # --------------------------------------------------------

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
                "Developer": "daruldark",
            },
        )

    selected_database = DATABASES[database]

    file_url = selected_database["url"]

    # --------------------------------------------------------
    # Database lookup
    # --------------------------------------------------------

    try:

        query = """
            SELECT *
            FROM read_parquet(?)
            WHERE CAST("Number" AS VARCHAR) = ?
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

        # ----------------------------------------------------
        # Not found
        # ----------------------------------------------------

        if row is None:

            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "database": selected_database["name"],
                    "database_file": selected_database["file"],
                    "matched": False,
                    "Developer": "daruldark",
                },
            )

        # ----------------------------------------------------
        # Found
        #
        # IMPORTANT:
        # Do not return the actual row because the dataset
        # contains personal information.
        # ----------------------------------------------------

        return {
            "status": "success",
            "database": selected_database["name"],
            "database_file": selected_database["file"],
            "matched": True,
            "columns_available": columns,
            "Developer": "daruldark",
        }

    except Exception as error:

        print("Database error:", error)

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Database operation failed.",
                "Developer": "daruldark",
            },
        )


# ============================================================
# LOCAL START
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.environ.get("PORT", 8080)
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )