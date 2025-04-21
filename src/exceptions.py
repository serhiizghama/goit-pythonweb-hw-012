import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=400,  # Convert 422 -> 400 Bad Request for consistency
        content={"detail": exc.errors()},
    )


async def integrity_exception_handler(request: Request, exc: IntegrityError):
    logger.error(f"Integrity Error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": "A record with this unique value already exists."},
    )


async def not_found_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"Not Found: {request.url} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail or "Resource not found"},
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )
