from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.schedule import router as schedule_router
from .api.control import router as control_router
from .database import Base, SessionLocal, engine
from .seed import seed_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(title="Boston Bioprocess", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:4200"], allow_methods=["*"], allow_headers=["*"])
app.include_router(schedule_router)
app.include_router(control_router)


@app.get("/health")
def health():
    return {"status": "ok"}
