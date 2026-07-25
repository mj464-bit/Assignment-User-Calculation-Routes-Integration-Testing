from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import users, calculations


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    yield


app = FastAPI(
    title="User & Calculation API",
    description="User registration/login and calculation BREAD endpoints",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
def read_health():
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(calculations.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    