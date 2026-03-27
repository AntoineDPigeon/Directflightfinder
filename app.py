"""Local development entry point. Imports the FastAPI app from api/index.py."""
import uvicorn
from api.index import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
