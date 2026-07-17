from fastapi import FastAPI

from app.database import Base, engine
from app.routers.requirements import router as requirements_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="ReqFlow Agent API",
    version="0.1.0",
)


app.include_router(requirements_router)


@app.get(
    "/health",
    tags=["system"],
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "reqflow-agent",
        "environment": "development",
    }