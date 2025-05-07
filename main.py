"""
Main FastAPI application definition.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import rules, evaluate, health, rule_categories
from app.core.config import settings
from app.utilities.logging import init_logging, logger


# Define lifespan handler (replacement for on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    """
    # Startup logic
    init_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    environment = os.environ.get("ENVIRONMENT", "development")
    logger.info(f"Environment: {environment}")

    yield  # Application runs here

    # Shutdown logic
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

# Create the FastAPI application with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan,  # Use lifespan instead of on_event
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware to capture and log request context
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Initialize context parameters
        entity_type = None
        rule_name = None
        category = None

        # Extract from query parameters if available
        if "entity_type" in request.query_params:
            entity_type = request.query_params["entity_type"]
        if "rule_name" in request.query_params:
            rule_name = request.query_params["rule_name"]
        if "category" in request.query_params:
            category = request.query_params["category"]

        # For POST requests, try to extract from request body
        # Note: We can't easily access the parsed body at middleware level
        # So path-based analysis is a better approach for middleware

        # Extract information from path for specific endpoints
        path = request.url.path
        path_parts = path.split("/")

        # Handle specific API patterns
        if "/api/v1/evaluate/failure-details/" in path:
            # Extract rule_name from URL pattern like /api/v1/evaluate/failure-details/{rule_name}
            rule_parts_index = path_parts.index("failure-details") + 1
            if rule_parts_index < len(path_parts):
                rule_name = path_parts[rule_parts_index]

        # Set initial context in logger (will be overridden by route handlers)
        logger.params.set(entity_type=entity_type, rule_name=rule_name, category=category)

        # Log the request
        logger.info(f"Request {request.method} {request.url.path}")

        # Process the request
        response = await call_next(request)

        # Log the response - by this point, the route handler will have set better context
        logger.info(f"Response {request.method} {request.url.path}: {response.status_code}")

        return response

app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(rules.router, prefix=settings.API_PREFIX, tags=["Rules"])
app.include_router(evaluate.router, prefix=settings.API_PREFIX, tags=["Evaluation"])
app.include_router(rule_categories.router, prefix=settings.API_PREFIX, tags=["Rule Categories"])

# Log router registration
logger.info("All routers registered successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)