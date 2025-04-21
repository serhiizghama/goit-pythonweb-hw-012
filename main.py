from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from src.api import contacts, users, auth
from src.exceptions import (
    validation_exception_handler,
    integrity_exception_handler,
    not_found_exception_handler,
    general_exception_handler,
)
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from src.conf.config import config as app_config


app = FastAPI()

limiter = Limiter(key_func=get_remote_address)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Requests rate limit exceeded"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router)
app.include_router(users.router)
app.include_router(auth.router)

app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(HTTPException, not_found_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/healthcheck")
async def healthchecker():
    return {"message": "The application is up and running!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
