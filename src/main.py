import uvicorn
from fastapi import FastAPI

from src.data import router as data_router
from src.login import router as login_router


def app() -> FastAPI:
    app = FastAPI()
    app.include_router(login_router)
    app.include_router(data_router)
    return app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
