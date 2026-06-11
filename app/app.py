import tomllib
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi_utils.tasks import repeat_every
from starlette.middleware.cors import CORSMiddleware

from .routes import restricted_router, limited_router, public_router

# Read version from pyproject.toml
def get_version():
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            # print(data["project"]["version"])

        return data["project"]["version"]

    except FileNotFoundError:
        return "0.1.0"  # fallback version


app = FastAPI(
    title="Hera-Care",
    description='Healthy life, Calm mind',
    version=get_version(),
    docs_url="/public/hera-care/apiv1/docs",
    redoc_url="/public/hera-care/apiv1/redoc",
    openapi_url="/public/hera-care/apiv1/openapi.json",
    contact={
        "name": "Parmida Sazegari",
        "url": "https://www.linkedin.com/in/parmida-sazegari/",
        "email": "parmidasazegari@gmail.com",
    }
)

# Mount static files FIRST (before routers)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Then include API routers
app.include_router(restricted_router)
app.include_router(limited_router)
app.include_router(public_router)

# Home page route
@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Cleanup task
@app.on_event("startup")
@repeat_every(seconds=60 * 30)
async def cleanup_old_sessions():
    """Periodic cleanup of old conversation sessions"""
    from app.services import ConversationManager
    ConversationManager.cleanup_old(max_age_minutes=60)

# Add after creating app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)