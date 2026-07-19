from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
import contextlib
import os

from .database import connect_to_mongo, close_mongo_connection
from .routers import orders, slots, admin, webhooks

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="RotiExpress API", lifespan=lifespan)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders.router)
app.include_router(slots.router)
app.include_router(admin.router)
app.include_router(webhooks.router)

@app.get("/api")
def read_root():
    return {"message": "Welcome to RotiExpress API"}

# Mount the frontend directory
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

@app.get("/admin")
async def serve_admin():
    return FileResponse(os.path.join(frontend_path, "admin.html"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
