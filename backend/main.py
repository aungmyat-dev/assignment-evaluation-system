from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from .routes import assignment_routes, auth_routes, submission_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings.upload_path
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"])
app.include_router(auth_routes.router)
app.include_router(assignment_routes.router)
app.include_router(submission_routes.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}
