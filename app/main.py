from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.exceptions import AppError

app = FastAPI()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exp: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exp.status_code,
        content={"error_code": exp.error_code, "message": exp.message},
    )


app.include_router(health_router)
app.include_router(api_router)
