"""
Example demonstrating log2fast_fastapi integration with a FastAPI application.

This example shows:
1. Basic logger setup
2. Module-based loggers
3. Request logging middleware
4. Context injection
5. Different log levels
"""

from fastapi import FastAPI, HTTPException

from log2fast_fastapi import (
    LogEnvironment,
    LogSettings,
    RequestLoggingMiddleware,
    get_logger,
    get_request_id,
)

# Configure logging for development
# In production, set LOG_ENVIRONMENT=production in .env
settings = LogSettings(
    log_environment=LogEnvironment.DEVELOPMENT,
    console_enabled=True,
    file_settings__enabled=True,
    module_name="example_app",
)

# Create FastAPI app
app = FastAPI(title="log2fast_fastapi Example")

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Get logger for this module
logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("Application starting up", extra_data={"version": "1.0.0"})


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Application shutting down")


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {"message": "Hello from log2fast_fastapi!", "request_id": get_request_id()}


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user by ID with logging."""
    logger.info("Fetching user", extra_data={"user_id": user_id})

    # Simulate user lookup
    if user_id == "123":
        logger.debug("User found in cache", extra_data={"user_id": user_id})
        return {"user_id": user_id, "name": "John Doe", "email": "john@example.com"}
    else:
        logger.warning("User not found", extra_data={"user_id": user_id})
        raise HTTPException(status_code=404, detail="User not found")


@app.post("/process")
async def process_data(data: dict):
    """Process data with detailed logging."""
    request_id = get_request_id()

    logger.info(
        "Processing data",
        extra_data={"request_id": request_id, "data_keys": list(data.keys())},
    )

    try:
        # Simulate processing
        result = {"status": "success", "processed_items": len(data)}

        logger.info(
            "Data processed successfully",
            extra_data={"request_id": request_id, "result": result},
        )

        return result

    except Exception as e:
        logger.exception(
            "Failed to process data",
            extra_data={"request_id": request_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Processing failed")


@app.get("/error")
async def trigger_error():
    """Endpoint that triggers an error for testing."""
    logger.warning("Error endpoint accessed - this will fail")

    try:
        # Intentional error
        result = 1 / 0
        print(result)
    except ZeroDivisionError:
        logger.exception(
            "Division by zero error",
            extra_data={"endpoint": "/error", "request_id": get_request_id()},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
