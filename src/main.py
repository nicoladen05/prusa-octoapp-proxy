import uvicorn
from fastapi import FastAPI

from login import (  # pyright: ignore[reportImplicitRelativeImport]
    router as login_router,
)


async def app():
    app = FastAPI()
    app.include_router(login_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
