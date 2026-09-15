from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

import duckdb
from huggingface_hub import HfFileSystem


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Number Lookup API",
    description="Number lookup API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://number-lookup-website.onrender.com",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ============================================================
# DUCKDB + HUGGING FACE
# ============================================================

con = duckdb.connect()

hf_fs = HfFileSystem(token=False)

con.register_filesystem(hf_fs)


# ============================================================
# PARQUET FILE
# ============================================================

FILE_URL = (
    "hf://buckets/daruldark/tele1/"
    "19M-BSNL_Mobile.parquet"
)


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
                "message": "Invalid endpoint. Use /?number=XXXXXXXXXX",
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
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def fetch_data(
    number: str = Query(
        default=None,
        description="Number to search"
    )
):

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
                "message": "Invalid parameter. Use /?number=XXXXXXXXXX",
                "Developer": "daruldark"
            }
        )

    # --------------------------------------------------------
    # Search database
    # --------------------------------------------------------

    try:

        query = f"""
            SELECT *
            FROM read_parquet('{FILE_URL}')
            WHERE "Number" = ?
        """

        result = con.execute(
            query,
            [number]
        )

        # ----------------------------------------------------
        # Get column names
        # ----------------------------------------------------

        columns = [
            description[0]
            for description in result.description
        ]

        # ----------------------------------------------------
        # Get matching rows
        # ----------------------------------------------------

        rows = result.fetchall()

        # ----------------------------------------------------
        # Convert rows to JSON objects
        # ----------------------------------------------------

        records = [
            dict(zip(columns, row))
            for row in rows
        ]

        # ----------------------------------------------------
        # No result
        # ----------------------------------------------------

        if not records:

            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "phone": number,
                    "Developer": "daruldark"
                }
            )

        # ----------------------------------------------------
        # Successful result
        # ----------------------------------------------------

        return {
            "status": "success",
            "Data": records,
            "Developer": "daruldark"
        }

    # --------------------------------------------------------
    # Database error
    # --------------------------------------------------------

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Database error: {str(e)}",
                "Developer": "daruldark"
            }
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "online",
        "service": "Number Lookup API",
        "Developer": "daruldark"
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import os
    import uvicorn

    port = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )