import uvicorn
from src.api.app import app

if __name__ == "__main__":
    # Run FastAPI application with uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
